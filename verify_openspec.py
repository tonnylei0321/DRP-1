#!/usr/bin/env python3
"""
OpenSpec 集成验证脚本。

验证 OpenSpec 集成的结构完整性。
"""

import json
import sys
from pathlib import Path


def check_directory_structure() -> bool:
    """检查目录结构完整性。"""
    print("📁 检查目录结构...")
    
    required_dirs = [
        "openspec",
        "openspec/config",
        "openspec/schemas", 
        "openspec/scripts",
        "openspec/tests",
    ]
    
    all_exists = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} (缺失)")
            all_exists = False
    
    return all_exists


def check_files() -> bool:
    """检查文件完整性。"""
    print("\n📄 检查文件完整性...")
    
    required_files = [
        "openspec/README.md",
        "openspec/DEVELOPMENT.md",
        "openspec/Makefile",
        "openspec/config/openapi-base.json",
        "openspec/scripts/generate_openapi.py",
        "openspec/scripts/validate_openapi.py",
        "openspec/tests/test_openapi.py",
    ]
    
    all_exists = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (缺失)")
            all_exists = False
    
    return all_exists


def check_pyproject_toml() -> bool:
    """检查 pyproject.toml 配置。"""
    print("\n⚙️  检查 pyproject.toml 配置...")
    
    try:
        import tomli
        
        with open("pyproject.toml", "rb") as f:
            config = tomli.load(f)
        
        # 检查依赖组
        if "dependency-groups" in config:
            dev_deps = config["dependency-groups"].get("dev", [])
            
            required_deps = [
                "openapi-spec-validator",
                "schemathesis", 
                "pytest-openapi",
                "openapi-pydantic",
            ]
            
            dev_dep_names = [dep if isinstance(dep, str) else list(dep.values())[0] for dep in dev_deps]
            
            all_present = True
            for dep in required_deps:
                if dep in dev_dep_names:
                    print(f"  ✅ {dep}")
                else:
                    print(f"  ❌ {dep} (缺失)")
                    all_present = False
            
            return all_present
        else:
            print("  ❌ 未找到 dependency-groups 配置")
            return False
            
    except ImportError:
        print("  ⚠️  无法解析 pyproject.toml (需要 tomli)")
        return True  # 跳过这个检查
    except Exception as e:
        print(f"  ❌ 解析 pyproject.toml 时出错: {e}")
        return False


def check_openapi_base_config() -> bool:
    """检查 OpenAPI 基础配置。"""
    print("\n🔧 检查 OpenAPI 基础配置...")
    
    try:
        config_path = Path("openspec/config/openapi-base.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 检查必需字段
        required_fields = ["openapi", "info", "servers", "tags", "paths", "components"]
        all_valid = True
        
        for field in required_fields:
            if field in config:
                print(f"  ✅ {field}")
            else:
                print(f"  ❌ {field} (缺失)")
                all_valid = False
        
        # 检查 info 字段
        if "info" in config:
            info = config["info"]
            info_fields = ["title", "version", "description"]
            for field in info_fields:
                if field in info:
                    print(f"  ✅ info.{field}")
                else:
                    print(f"  ❌ info.{field} (缺失)")
                    all_valid = False
        
        return all_valid
        
    except Exception as e:
        print(f"  ❌ 检查 OpenAPI 配置时出错: {e}")
        return False


def check_scripts() -> bool:
    """检查脚本文件。"""
    print("\n📜 检查脚本文件...")
    
    scripts = [
        "openspec/scripts/generate_openapi.py",
        "openspec/scripts/validate_openapi.py",
    ]
    
    all_valid = True
    for script_path in scripts:
        path = Path(script_path)
        if path.exists():
            # 检查文件是否可读
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read(100)  # 只读前100个字符
                if content.startswith("#!/usr/bin/env python3"):
                    print(f"  ✅ {script_path} (格式正确)")
                else:
                    print(f"  ⚠️  {script_path} (缺少 shebang)")
            except Exception as e:
                print(f"  ❌ {script_path} (读取失败: {e})")
                all_valid = False
        else:
            print(f"  ❌ {script_path} (缺失)")
            all_valid = False
    
    return all_valid


def main():
    """主函数。"""
    print("🔍 开始验证 OpenSpec 集成...")
    print("=" * 50)
    
    # 切换到 backend 目录
    backend_dir = Path("backend")
    if backend_dir.exists():
        os.chdir(backend_dir)
        print(f"📂 切换到目录: {backend_dir.absolute()}")
    else:
        print(f"❌ backend 目录不存在: {backend_dir.absolute()}")
        return False
    
    checks = [
        ("目录结构", check_directory_structure),
        ("文件完整性", check_files),
        ("pyproject.toml 配置", check_pyproject_toml),
        ("OpenAPI 基础配置", check_openapi_base_config),
        ("脚本文件", check_scripts),
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n{'='*30}")
        print(f"检查: {check_name}")
        print(f"{'='*30}")
        result = check_func()
        results.append((check_name, result))
    
    # 汇总结果
    print(f"\n{'='*50}")
    print("📊 验证结果汇总")
    print(f"{'='*50}")
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{check_name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 OpenSpec 集成验证通过!")
        print("\n下一步:")
        print("1. 安装依赖: pip install -e '.[dev]'")
        print("2. 生成规范: make generate")
        print("3. 验证规范: make validate")
        print("4. 运行测试: make test")
    else:
        print("⚠️  OpenSpec 集成验证失败，请检查上述问题。")
        sys.exit(1)


if __name__ == "__main__":
    import os
    main()