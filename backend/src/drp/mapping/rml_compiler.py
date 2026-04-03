"""MappingSpec → RML（RDF Mapping Language）确定性编译器。

将 YAML 格式的映射规范编译为 W3C RML Turtle 格式。
"""


_RML_PREFIXES = """\
@prefix rr: <http://www.w3.org/ns/r2rml#> .
@prefix rml: <http://semweb.mmlab.be/ns/rml#> .
@prefix ql: <http://semweb.mmlab.be/ns/ql#> .
@prefix ctio: <urn:ctio:> .
@prefix fibo-fbc-pas-caa: <https://spec.edmcouncil.org/fibo/ontology/FBC/ProductsAndServices/ClientsAndAccounts/> .
@prefix fibo-be-le-lp: <https://spec.edmcouncil.org/fibo/ontology/BE/LegalEntities/LEIEntities/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

"""

_TYPE_TO_XSD = {
    "INT": "xsd:integer",
    "INTEGER": "xsd:integer",
    "BIGINT": "xsd:long",
    "SMALLINT": "xsd:short",
    "DECIMAL": "xsd:decimal",
    "NUMERIC": "xsd:decimal",
    "FLOAT": "xsd:float",
    "DOUBLE": "xsd:double",
    "VARCHAR": "xsd:string",
    "CHAR": "xsd:string",
    "TEXT": "xsd:string",
    "NVARCHAR": "xsd:string",
    "DATE": "xsd:date",
    "TIMESTAMP": "xsd:dateTime",
    "DATETIME": "xsd:dateTime",
    "BOOLEAN": "xsd:boolean",
    "BOOL": "xsd:boolean",
}


def _xsd_type(data_type: str) -> str:
    base = data_type.upper().split("(")[0].strip()
    return _TYPE_TO_XSD.get(base, "xsd:string")


def _safe_name(s: str) -> str:
    """将任意字符串转为合法的 Turtle 局部名。"""
    return s.replace("-", "_").replace(".", "_").replace(" ", "_")


def compile_to_rml(mappings: list[dict], source_table: str, db_uri: str = "urn:source:db") -> str:
    """将映射字典列表编译为 RML Turtle 字符串。

    Args:
        mappings: parse_mapping_yaml 返回的字典列表
        source_table: 主表名（用于生成 TriplesMap 名称）
        db_uri: 源数据库逻辑标识符

    Returns:
        RML Turtle 格式字符串
    """
    # 按 source_table 分组
    tables: dict[str, list[dict]] = {}
    for m in mappings:
        tbl = m.get("source_table", source_table)
        tables.setdefault(tbl, []).append(m)

    parts = [_RML_PREFIXES]

    for tbl, cols in tables.items():
        map_name = f"<#{_safe_name(tbl)}TriplesMap>"
        parts.append(f"{map_name}")
        parts.append(f"    a rr:TriplesMap ;")
        parts.append(f"    rml:logicalSource [")
        parts.append(f"        rml:source <{db_uri}> ;")
        parts.append(f"        rml:referenceFormulation ql:CSV ;")
        parts.append(f"        rml:iterator \"{tbl}\" ;")
        parts.append(f"    ] ;")
        parts.append(f"    rr:subjectMap [")
        parts.append(f"        rr:template \"urn:entity:{tbl}/{{id}}\" ;")
        parts.append(f"        rr:class ctio:{_safe_name(tbl)} ;")
        parts.append(f"    ] ;")

        for col in cols:
            target = col.get("target_property")
            if not target:
                continue
            field = col["source_field"]
            xsd = _xsd_type(col.get("data_type", "VARCHAR"))
            transform = col.get("transform_rule", "")

            parts.append(f"    rr:predicateObjectMap [")
            parts.append(f"        rr:predicate {target} ;")
            parts.append(f"        rr:objectMap [")
            parts.append(f"            rml:reference \"{field}\" ;")
            parts.append(f"            rr:datatype {xsd} ;")
            if transform:
                parts.append(f"            # 转换规则: {transform}")
            parts.append(f"        ] ;")
            parts.append(f"    ] ;")

        parts.append(".\n")

    return "\n".join(parts)
