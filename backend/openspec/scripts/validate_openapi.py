#!/usr/bin/env python3
"""
验证 OpenAPI 规范。

该脚本验证 OpenAPI 规范的完整性和一致性。
"""

import json
import sys
from pathlib import Path

from openapi_spec_validator import validate_spec


def load_openapi_spec(spec_path: Path) -> dict:
    """加载 OpenAPI 规范文件。"""
    with open(spec_path, "r", encoding="utf-8") as f:
        if spec_path.suffix == ".json":
            return json.load(f)
        else:
            import yaml
            return yaml.safe_load(f)


def validate_spec_structure(spec: dict) -> list[str]:
    """验证规范结构完整性。"""
    errors = []
    
    # 检查必需字段
    required_fields = ["openapi", "info", "paths"]
    for field in required_fields:
        if field not in spec:
            errors.append(f"缺少必需字段: {field}")
    
    # 检查 info 字段
    if "info" in spec:
        info = spec["info"]
        info_required = ["title", "version"]
        for field in info_required:
            if field not in info:
                errors.append(f"info 缺少必需字段: {field}")
    
    # 检查 paths
    if "paths" in spec:
        paths = spec["paths"]
        if not isinstance(paths, dict):
            errors.append("paths 必须是字典类型")
        elif len(paths) == 0:
            errors.append("paths 不能为空")
        else:
            # 检查每个路径的操作
            for path, path_item in paths.items():
                if not path.startswith("/"):
                    errors.append(f"路径必须以 '/' 开头: {path}")
                
                # 检查是否有 HTTP 方法
                http_methods = ["get", "post", "put", "delete", "patch", "head", "options", "trace"]
                has_method = any(method in path_item for method in http_methods)
                if not has_method:
                    errors.append(f"路径没有定义 HTTP 方法: {path}")
    
    # 检查 components
    if "components" in spec:
        components = spec["components"]
        if not isinstance(components, dict):
            errors.append("components 必须是字典类型")
    
    return errors


def validate_responses(spec: dict) -> list[str]:
    """验证响应定义。"""
    errors = []
    
    if "paths" not in spec:
        return errors
    
    for path, path_item in spec["paths"].items():
        for method, operation in path_item.items():
            if method.lower() not in ["get", "post", "put", "delete", "patch", "head", "options", "trace"]:
                continue
            
            # 检查是否有 responses
            if "responses" not in operation:
                errors.append(f"操作 {method.upper()} {path} 缺少 responses 定义")
                continue
            
            responses = operation["responses"]
            
            # 检查是否有成功响应
            success_codes = ["200", "201", "202", "204"]
            has_success = any(code in responses for code in success_codes)
            if not has_success:
                errors.append(f"操作 {method.upper()} {path} 缺少成功响应 (200, 201, 202, 204)")
            
            # 检查是否有错误响应
            error_codes = ["400", "401", "403", "404", "422", "500"]
            has_error = any(code in responses for code in error_codes)
            if not has_error:
                errors.append(f"操作 {method.upper()} {path} 缺少错误响应 (4xx 或 5xx)")
    
    return errors


def validate_parameters(spec: dict) -> list[str]:
    """验证参数定义。"""
    errors = []
    
    if "paths" not in spec:
        return errors
    
    for path, path_item in spec["paths"].items():
        for method, operation in path_item.items():
            if method.lower() not in ["get", "post", "put", "delete", "patch", "head", "options", "trace"]:
                continue
            
            # 检查路径参数是否在路径中定义
            if "parameters" in operation:
                for param in operation["parameters"]:
                    if param.get("in") == "path":
                        param_name = param.get("name", "")
                        if param_name not in path:
                            errors.append(f"路径参数 '{param_name}' 不在路径中: {path}")
    
    return errors


def main():
    """主函数。"""
    try:
        print("🔍 开始验证 OpenAPI 规范...")
        
        # 查找规范文件
        spec_dir = Path(__file__).parent.parent
        spec_files = list(spec_dir.glob("openapi.*"))
        
        if not spec_files:
            print("❌ 未找到 OpenAPI 规范文件")
            print("请先运行 generate_openapi.py 生成规范")
            sys.exit(1)
        
        spec_path = spec_files[0]
        print(f"📄 加载规范文件: {spec_path}")
        
        # 加载规范
        spec = load_openapi_spec(spec_path)
        
        # 使用库验证规范
        print("🔬 使用 openapi-spec-validator 验证...")
        try:
            validate_spec(spec)
            print("✅ 规范语法验证通过")
        except Exception as e:
            print(f"❌ 规范语法验证失败: {e}")
            sys.exit(1)
        
        # 自定义验证
        print("🔬 执行自定义验证...")
        
        all_errors = []
        
        # 验证结构
        structure_errors = validate_spec_structure(spec)
        if structure_errors:
            all_errors.extend(structure_errors)
            print("❌ 结构验证失败")
            for error in structure_errors:
                print(f"  - {error}")
        else:
            print("✅ 结构验证通过")
        
        # 验证响应
        response_errors = validate_responses(spec)
        if response_errors:
            all_errors.extend(response_errors)
            print("❌ 响应验证失败")
            for error in response_errors:
                print(f"  - {error}")
        else:
            print("✅ 响应验证通过")
        
        # 验证参数
        parameter_errors = validate_parameters(spec)
        if parameter_errors:
            all_errors.extend(parameter_errors)
            print("❌ 参数验证失败")
            for error in parameter_errors:
                print(f"  - {error}")
        else:
            print("✅ 参数验证通过")
        
        # 输出统计信息
        print("\n📊 验证统计:")
        print(f"  - 总路径数: {len(spec.get('paths', {}))}")
        print(f"  - 总操作数: {sum(len(path_item) for path_item in spec.get('paths', {}).values())}")
        print(f"  - 验证错误数: {len(all_errors)}")
        
        if all_errors:
            print("\n❌ OpenAPI 规范验证失败")
            sys.exit(1)
        else:
            print("\n✅ OpenAPI 规范验证通过!")
            
    except Exception as e:
        print(f"❌ 验证 OpenAPI 规范时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()