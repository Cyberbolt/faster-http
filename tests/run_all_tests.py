#!/usr/bin/env python3
"""
运行所有faster-http功能测试
"""

import sys
import os
import subprocess
import importlib.util
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_test_module(module_path, module_name):
    """运行单个测试模块"""
    print(f"\n{'='*60}")
    print(f"🧪 运行 {module_name} 测试")
    print(f"{'='*60}")
    
    try:
        # 动态导入测试模块
        spec = importlib.util.spec_from_file_location("test_module", module_path)
        test_module = importlib.util.module_from_spec(spec)
        
        # 设置模块路径
        original_sys_path = sys.path.copy()
        test_dir = str(module_path.parent)
        if test_dir not in sys.path:
            sys.path.insert(0, test_dir)
        
        try:
            spec.loader.exec_module(test_module)
            
            # 调用main函数
            if hasattr(test_module, 'main'):
                test_module.main()
                print(f"✅ {module_name} 测试完成")
                return True
            else:
                print(f"⚠️ {module_name} 没有main函数")
                return False
                
        finally:
            # 恢复sys.path
            sys.path = original_sys_path
            
    except Exception as e:
        print(f"❌ {module_name} 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_pytest_tests():
    """运行pytest测试"""
    print(f"\n{'='*60}")
    print("🧪 运行 Pytest 单元测试")
    print(f"{'='*60}")
    
    try:
        # 运行pytest
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(project_root / "tests" / "unit"),
            str(project_root / "tests" / "integration"),
            "-v"
        ], cwd=project_root, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print("✅ Pytest 测试完成")
            return True
        else:
            print(f"❌ Pytest 测试失败 (退出码: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ Pytest 测试异常: {e}")
        return False

def main():
    """运行所有测试"""
    print("🚀 开始运行 faster-http 全面测试套件")
    print(f"📁 项目根目录: {project_root}")
    
    # 检查项目是否已编译
    print("\n📦 检查项目编译状态...")
    try:
        import faster_http
        print("✅ faster-http 模块已加载")
    except ImportError as e:
        print(f"❌ faster-http 模块加载失败: {e}")
        print("请先运行: uv run maturin develop")
        return False
    
    # 定义测试模块
    features_dir = project_root / "tests" / "features"
    test_modules = [
        (features_dir / "test_event_hooks.py", "Event Hooks"),
        (features_dir / "test_ssl_config.py", "SSL配置"),
        (features_dir / "test_transport.py", "Transport自定义"),
        (features_dir / "test_proxy.py", "代理配置"),
        (features_dir / "test_comprehensive.py", "综合功能"),
    ]
    
    # 运行结果统计
    results = []
    
    # 运行功能测试
    for module_path, module_name in test_modules:
        if module_path.exists():
            success = run_test_module(module_path, module_name)
            results.append((module_name, success))
        else:
            print(f"⚠️ 测试文件不存在: {module_path}")
            results.append((module_name, False))
    
    # 运行pytest测试
    pytest_success = run_pytest_tests()
    results.append(("Pytest单元测试", pytest_success))
    
    # 测试结果总结
    print(f"\n{'='*60}")
    print("📊 测试结果总结")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 总体结果: {passed}/{total} 测试套件通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！faster-http 功能完整且稳定！")
        print("\n✨ 已验证的功能:")
        print("  🎣 Event Hooks系统")
        print("  🔒 高级SSL配置")
        print("  🚚 Transport自定义")
        print("  🌐 高级代理配置")
        print("  🔄 完整httpx兼容性")
        print("  🧪 单元和集成测试")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)