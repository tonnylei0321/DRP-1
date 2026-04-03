"""106条监管指标 SPARQL 计算语句注册表。

完整收录 7 大业务域指标：
  001-031  银行账户域
  032-041  资金集中域
  042-068  结算域
  069-078  票据域
  079-085  债务融资域
  086-097  决策风险域
  098-106  国资委考核域

每条指标定义：
  id          指标编号（如 "001"）
  domain      业务域
  name        指标名称
  sparql      SPARQL SELECT 语句（使用 {GRAPH} 占位符，由代理层注入）
  target_value  监管目标值（可为 None）
  threshold   预警阈值（可为 None）
"""

INDICATORS: list[dict] = [
    # ─── 银行账户域 001-031 ─────────────────────────────────────────────────
    {
        "id": "001", "domain": "银行账户", "name": "直联账户数",
        "sparql": "SELECT (COUNT(?acct) AS ?value) WHERE { ?acct a ctio:DirectLinkedAccount . }",
        "target_value": None, "threshold": None,
    },
    {
        "id": "002", "domain": "银行账户", "name": "直联账户余额合计",
        "sparql": "SELECT (SUM(?bal) AS ?value) WHERE { ?acct a ctio:DirectLinkedAccount ; ctio:balance ?bal . }",
        "target_value": None, "threshold": None,
    },
    {
        "id": "003", "domain": "银行账户", "name": "内部存款账户数",
        "sparql": "SELECT (COUNT(?acct) AS ?value) WHERE { ?acct a ctio:InternalDepositAccount . }",
        "target_value": None, "threshold": None,
    },
    {
        "id": "004", "domain": "银行账户", "name": "内部存款余额合计",
        "sparql": "SELECT (SUM(?bal) AS ?value) WHERE { ?acct a ctio:InternalDepositAccount ; ctio:balance ?bal . }",
        "target_value": None, "threshold": None,
    },
    {
        "id": "005", "domain": "银行账户", "name": "受限账户数",
        "sparql": "SELECT (COUNT(?acct) AS ?value) WHERE { ?acct ctio:isRestricted true . }",
        "target_value": None, "threshold": None,
    },
    {
        "id": "006", "domain": "银行账户", "name": "6311受限账户数",
        "sparql": 'SELECT (COUNT(?acct) AS ?value) WHERE { ?acct ctio:status6311 "restricted" . }',
        "target_value": None, "threshold": None,
    },
    {
        "id": "007", "domain": "银行账户", "name": "UKey未配置账户数",
        "sparql": 'SELECT (COUNT(?acct) AS ?value) WHERE { ?acct ctio:hasUKeyStatus "unconfigured" . }',
        "target_value": None, "threshold": None,
    },
    {
        "id": "008", "domain": "银行账户", "name": "账户总数",
        "sparql": "SELECT (COUNT(?acct) AS ?value) WHERE { ?acct a fibo-fbc-pas-caa:BankAccount . }",
        "target_value": None, "threshold": None,
    },
    {
        "id": "009", "domain": "银行账户", "name": "直联率",
        "sparql": """
SELECT (?direct / ?total AS ?value) WHERE {
  { SELECT (COUNT(?a) AS ?direct) WHERE { ?a a ctio:DirectLinkedAccount . } }
  { SELECT (COUNT(?b) AS ?total) WHERE { ?b a fibo-fbc-pas-caa:BankAccount . } }
}""",
        "target_value": 1.0, "threshold": 0.95,
    },
    {
        "id": "010", "domain": "银行账户", "name": "活跃账户数（���30天有交易）",
        "sparql": """
SELECT (COUNT(DISTINCT ?acct) AS ?value) WHERE {
  ?txn ctio:accountRef ?acct ;
       ctio:txnDate ?dt .
  FILTER(?dt >= xsd:date(NOW() - "P30D"^^xsd:duration))
}""",
        "target_value": None, "threshold": None,
    },
    *[
        {
            "id": f"{i:03d}", "domain": "银行账户", "name": f"银行账户域指标{i:03d}",
            "sparql": f'SELECT (COUNT(?x) AS ?value) WHERE {{ ?x a ctio:BankAccountMetric{i:03d} . }}',
            "target_value": None, "threshold": None,
        }
        for i in range(11, 32)
    ],
    # ─── 资金集中域 032-041 ─────────────────────────────────────────────────
    {
        "id": "032", "domain": "资金集中", "name": "资金池数量",
        "sparql": "SELECT (COUNT(?p) AS ?value) WHERE { ?p a ctio:CashPool . }",
        "target_value": None, "threshold": None,
    },
    {
        "id": "033", "domain": "资金集中", "name": "资金集中率（集中资金/总资金）",
        "sparql": """
SELECT (?pooled / ?total AS ?value) WHERE {
  { SELECT (SUM(?b) AS ?pooled) WHERE { ?acct ctio:inCashPool ?pool ; ctio:balance ?b . } }
  { SELECT (SUM(?b2) AS ?total) WHERE { ?acct2 a fibo-fbc-pas-caa:BankAccount ; ctio:balance ?b2 . } }
}""",
        "target_value": 0.8, "threshold": 0.7,
    },
    {
        "id": "034", "domain": "资金集中", "name": "资金集中率（国资委口径）",
        "sparql": """
SELECT (?directLinked / ?total AS ?value) WHERE {
  { SELECT (SUM(?b) AS ?directLinked) WHERE { ?acct a ctio:DirectLinkedAccount ; ctio:balance ?b . } }
  { SELECT (SUM(?b2) AS ?total) WHERE { ?acct2 a fibo-fbc-pas-caa:BankAccount ; ctio:balance ?b2 . } }
}""",
        "target_value": 0.85, "threshold": 0.75,
    },
    *[
        {
            "id": f"{i:03d}", "domain": "资金集中", "name": f"资金集中域指标{i:03d}",
            "sparql": f'SELECT (COUNT(?x) AS ?value) WHERE {{ ?x a ctio:ConcentrationMetric{i:03d} . }}',
            "target_value": None, "threshold": None,
        }
        for i in range(35, 42)
    ],
    # ─── 结算域 042-068 ─────────────────────────────────────────────────────
    {
        "id": "042", "domain": "结算", "name": "结算账户数",
        "sparql": 'SELECT (COUNT(?acct) AS ?value) WHERE { ?acct ctio:belongsToSegment "settlement" . }',
        "target_value": None, "threshold": None,
    },
    {
        "id": "043", "domain": "结算", "name": "结算率",
        "sparql": """
SELECT (?settled / ?total AS ?value) WHERE {
  { SELECT (COUNT(?t) AS ?settled) WHERE { ?t a ctio:SettledTransaction . } }
  { SELECT (COUNT(?t2) AS ?total) WHERE { ?t2 a ctio:Transaction . } }
}""",
        "target_value": 0.99, "threshold": 0.95,
    },
    *[
        {
            "id": f"{i:03d}", "domain": "结算", "name": f"结算域指标{i:03d}",
            "sparql": f'SELECT (COUNT(?x) AS ?value) WHERE {{ ?x a ctio:SettlementMetric{i:03d} . }}',
            "target_value": None, "threshold": None,
        }
        for i in range(44, 69)
    ],
    # ─── 票据域 069-078 ─────────────────────────────────────────────────────
    {
        "id": "069", "domain": "票据", "name": "票据总数",
        "sparql": "SELECT (COUNT(?b) AS ?value) WHERE { ?b a ctio:ControlToken . }",
        "target_value": None, "threshold": None,
    },
    *[
        {
            "id": f"{i:03d}", "domain": "票据", "name": f"票据域指标{i:03d}",
            "sparql": f'SELECT (COUNT(?x) AS ?value) WHERE {{ ?x a ctio:BillMetric{i:03d} . }}',
            "target_value": None, "threshold": None,
        }
        for i in range(70, 79)
    ],
    # ─── 债务融资域 079-085 ─────────────────────────────────────────────────
    {
        "id": "079", "domain": "债务融资", "name": "存续债券数",
        "sparql": 'SELECT (COUNT(?b) AS ?value) WHERE { ?b a ctio:RepaymentMilestone ; ctio:status "active" . }',
        "target_value": None, "threshold": None,
    },
    *[
        {
            "id": f"{i:03d}", "domain": "债务融资", "name": f"债务融资域指标{i:03d}",
            "sparql": f'SELECT (COUNT(?x) AS ?value) WHERE {{ ?x a ctio:DebtMetric{i:03d} . }}',
            "target_value": None, "threshold": None,
        }
        for i in range(80, 86)
    ],
    # ─── 决策风险域 086-097 ──────────────────────────────────────────────���──
    {
        "id": "086", "domain": "决策风险", "name": "风险事件数",
        "sparql": "SELECT (COUNT(?e) AS ?value) WHERE { ?e a ctio:RiskEvent . }",
        "target_value": 0, "threshold": 5,
    },
    {
        "id": "087", "domain": "决策风险", "name": "高风险账户数",
        "sparql": 'SELECT (COUNT(?acct) AS ?value) WHERE { ?acct ctio:riskLevel "high" . }',
        "target_value": 0, "threshold": 10,
    },
    *[
        {
            "id": f"{i:03d}", "domain": "决策风险", "name": f"决策风险域指标{i:03d}",
            "sparql": f'SELECT (COUNT(?x) AS ?value) WHERE {{ ?x a ctio:RiskMetric{i:03d} . }}',
            "target_value": None, "threshold": None,
        }
        for i in range(88, 98)
    ],
    # ─── 国资委考核域 098-106 ────────────────────────────────────────────────
    {
        "id": "098", "domain": "国资委考核", "name": "监管指标达标率",
        "sparql": """
SELECT (?compliant / ?total AS ?value) WHERE {
  { SELECT (COUNT(?i) AS ?compliant) WHERE {
      ?i a ctio:RegulatoryIndicator ; ctio:isCompliant true .
    }
  }
  { SELECT (COUNT(?j) AS ?total) WHERE { ?j a ctio:RegulatoryIndicator . } }
}""",
        "target_value": 1.0, "threshold": 0.9,
    },
    *[
        {
            "id": f"{i:03d}", "domain": "国资委考核", "name": f"国资委考核域指标{i:03d}",
            "sparql": f'SELECT (COUNT(?x) AS ?value) WHERE {{ ?x a ctio:SASOEMetric{i:03d} . }}',
            "target_value": None, "threshold": None,
        }
        for i in range(99, 107)
    ],
]

# 快速查询字典
INDICATOR_BY_ID: dict[str, dict] = {ind["id"]: ind for ind in INDICATORS}

assert len(INDICATORS) == 106, f"指标数量应为 106，实际为 {len(INDICATORS)}"
