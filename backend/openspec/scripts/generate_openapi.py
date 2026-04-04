#!/usr/bin/env python3
"""
生成 OpenAPI 规范文件。

该脚本从 FastAPI 应用生成 OpenAPI 规范，并与基础配置合并。
"""

import json
import sys
from pathlib import Path

import yaml
from openapi_spec_validator import validate_spec

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from drp.main import app


def generate_openapi_spec() -> dict:
    """从 FastAPI 应用生成 OpenAPI 规范。"""
    openapi_schema = app.openapi()
    return openapi_schema


def load_base_config() -> dict:
    """加载基础 OpenAPI 配置。"""
    config_path = Path(__file__).parent.parent / "config" / "openapi-base.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def merge_specs(base_spec: dict, generated_spec: dict) -> dict:
    """合并基础配置和生成的规范。"""
    # 保留基础配置中的 servers、tags、components 等
    merged = base_spec.copy()
    
    # 更新 info 部分（保留版本等信息）
    merged["info"].update(generated_spec.get("info", {}))
    
    # 合并 paths
    merged["paths"] = generated_spec.get("paths", {})
    
    # 合并 components
    if "components" in generated_spec:
        for component_type, components in generated_spec["components"].items():
            if component_type not in merged["components"]:
                merged["components"][component_type] = {}
            merged["components"][component_type].update(components)
    
    return merged


def validate_openapi_spec(spec: dict) -> bool:
    """验证 OpenAPI 规范。"""
    try:
        validate_spec(spec)
        print("✅ OpenAPI 规范验证通过")
        return True
    except Exception as e:
        print(f"❌ OpenAPI 规范验证失败: {e}")
        return False


def save_spec(spec: dict, output_dir: Path) -> None:
    """保存规范到文件。"""
    # 保存为 JSON
    json_path = output_dir / "openapi.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    print(f"📄 OpenAPI 规范已保存到: {json_path}")
    
    # 保存为 YAML
    yaml_path = output_dir / "openapi.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(spec, f, allow_unicode=True, sort_keys=False)
    print(f"📄 OpenAPI 规范已保存到: {yaml_path}")


def main():
    """主函数。"""
    try:
        print("🚀 开始生成 OpenAPI 规范...")
        
        # 加载基础配置
        print("📋 加载基础配置...")
        base_spec = load_base_config()
        
        # 生成 OpenAPI 规范
        print("🔧 从 FastAPI 应用生成规范...")
        generated_spec = generate_openapi_spec()
        
        # 合并规范
        print("🔄 合并规范...")
        merged_spec = merge_specs(base_spec, generated_spec)
        
        # 验证规范
        print("🔍 验证规范...")
        if not validate_openapi_spec(merged_spec):
            sys.exit(1)
        
        # 保存规范
        output_dir = Path(__file__).parent.parent
        save_spec(merged_spec, output_dir)
        
        # 输出统计信息
        print("\n📊 规范统计:")
        print(f"  - 路径数量: {len(merged_spec.get('paths', {}))}")
        print(f"  - 组件 schemas: {len(merged_spec.get('components', {}).get('schemas', {}))}")
        print(f"  - 标签数量: {len(merged_spec.get('tags', []))}")
        
        print("\n✅ OpenAPI 规范生成完成!")
        
    except Exception as e:
        print(f"❌ 生成 OpenAPI 规范时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()