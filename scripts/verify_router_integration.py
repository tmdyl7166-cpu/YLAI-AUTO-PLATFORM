#!/usr/bin/env python3
"""
快速验证脚本：验证 router_registry 集成效果

用法: python scripts/verify_router_integration.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def verify_imports():
    """验证导入完整性"""
    print("\n📋 验证导入完整性...")
    try:
        from backend.api.router_registry import register_routers, get_router_info
        print("  ✅ router_registry 导入成功")
        return True
    except ImportError as e:
        print(f"  ❌ 导入失败: {e}")
        return False

def verify_syntax():
    """验证 Python 语法"""
    print("\n📋 验证 Python 语法...")
    import py_compile
    
    files_to_check = [
        "backend/app.py",
        "backend/api/router_registry.py",
        "backend/core/response.py",
    ]
    
    all_ok = True
    for filepath in files_to_check:
        full_path = PROJECT_ROOT / filepath
        try:
            py_compile.compile(str(full_path), doraise=True)
            print(f"  ✅ {filepath}")
        except py_compile.PyCompileError as e:
            print(f"  ❌ {filepath}: {e}")
            all_ok = False
    
    return all_ok

def count_imports():
    """统计导入语句数量"""
    print("\n📊 统计代码变化...")
    
    app_py = PROJECT_ROOT / "backend/app.py"
    router_registry = PROJECT_ROOT / "backend/api/router_registry.py"
    
    # 统计 app.py
    with open(app_py) as f:
        app_lines = f.readlines()
    
    total_lines = len(app_lines)
    
    # 统计旧导入是否完全清理
    old_imports = [
        "from backend.api.pipeline import",
        "from backend.api.security import",
        "from backend.api.auth import router",
        "app.include_router(simple_pipeline_router)",
        "app.include_router(security_router)",
    ]
    
    found_old = []
    for old_import in old_imports:
        for line in app_lines:
            if old_import in line and not line.strip().startswith("#"):
                found_old.append(old_import)
                break
    
    print(f"  📄 backend/app.py: {total_lines} 行")
    print(f"     原始: 737 行 → 现在: {total_lines} 行 (减少 {737 - total_lines} 行)")
    
    # 验证新的统一导入
    has_new_import = False
    for line in app_lines:
        if "from backend.api.router_registry import register_routers" in line:
            has_new_import = True
            break
    
    if has_new_import:
        print(f"  ✅ 新的统一导入已添加")
    else:
        print(f"  ❌ 未找到新的统一导入")
    
    if found_old:
        print(f"  ❌ 发现 {len(found_old)} 个旧导入未清理:")
        for old in found_old[:3]:
            print(f"     - {old}")
        return False
    else:
        print(f"  ✅ 所有旧导入已清理")
    
    return True

def verify_router_registry():
    """验证 router_registry 功能"""
    print("\n📋 验证 router_registry 功能...")
    
    try:
        from backend.api.router_registry import ROUTER_REGISTRY, OPTIONAL_ROUTERS, get_router_info
        
        print(f"  📊 ROUTER_REGISTRY: {len(ROUTER_REGISTRY)} 个路由")
        for name, config in list(ROUTER_REGISTRY.items())[:5]:
            status = "✅" if config.get('enabled') else "⚪"
            print(f"     {status} {name}: {config.get('module', 'N/A')}")
        if len(ROUTER_REGISTRY) > 5:
            print(f"     ... 还有 {len(ROUTER_REGISTRY) - 5} 个路由")
        
        print(f"  📊 OPTIONAL_ROUTERS: {len(OPTIONAL_ROUTERS)} 个可选路由")
        for name, config in list(OPTIONAL_ROUTERS.items())[:3]:
            status = "✅" if config.get('enabled') else "⏭️"
            print(f"     {status} {name}: {config.get('module', 'N/A')}")
        if len(OPTIONAL_ROUTERS) > 3:
            print(f"     ... 还有 {len(OPTIONAL_ROUTERS) - 3} 个可选路由")
        
        info = get_router_info()
        print(f"  📋 router_info 生成成功: {len(info)} 个路由信息")
        
        return True
    except Exception as e:
        print(f"  ❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主验证流程"""
    print("=" * 60)
    print("🚀 router_registry 集成验证工具")
    print("=" * 60)
    
    results = {
        "导入完整性": verify_imports(),
        "Python 语法": verify_syntax(),
        "代码统计": count_imports(),
        "Router 功能": verify_router_registry(),
    }
    
    print("\n" + "=" * 60)
    print("📊 验收结果摘要")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} - {name}")
    
    print("=" * 60)
    print(f"总体结果: {passed}/{total} 项通过")
    print("=" * 60)
    
    if passed == total:
        print("\n✅ 所有验收项通过！router_registry 集成成功！")
        print("\n下一步:")
        print("  1. 启动后端服务: python -m uvicorn backend.app:app --reload")
        print("  2. 访问 Swagger UI: http://localhost:8001/docs")
        print("  3. 验证所有路由正确显示")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 项验收失败，请检查上面的错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())
