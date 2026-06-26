#!/usr/bin/env python3
"""
一键运行完整测试和启动服务
"""

import subprocess
import sys
import os
import time

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def run_command(cmd, description, cwd=None):
    print(f"📌 {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {description} - 成功")
            return True
        else:
            print(f"❌ {description} - 失败")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} - 错误: {e}")
        return False

def main():
    print_header("🚀 AI圆桌讨论系统 - 自动化测试与启动")
    
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    
    # 步骤1：安装测试依赖
    print_header("步骤1: 安装测试依赖")
    if not run_command(
        "pip install -q -r requirements-test.txt",
        "安装测试依赖",
        cwd=backend_dir
    ):
        print("\n⚠️  依赖安装失败，但继续运行测试...")
    
    # 步骤2：运行测试
    print_header("步骤2: 运行测试套件")
    test_success = run_command(
        "pytest tests/ -v --tb=short",
        "执行pytest测试",
        cwd=backend_dir
    )
    
    # 步骤3：生成覆盖率报告
    if test_success:
        print_header("步骤3: 生成覆盖率报告")
        run_command(
            "pytest tests/ --cov=services --cov=routes --cov-report=html --cov-report=term",
            "生成覆盖率报告",
            cwd=backend_dir
        )
        print(f"\n📊 覆盖率报告已生成: {backend_dir}/htmlcov/index.html")
    
    # 步骤4：询问是否启动服务器
    print_header("步骤4: 启动服务器")
    print("测试完成！")
    
    if test_success:
        print("\n✅ 所有测试通过！")
        response = input("\n是否启动后端服务器？(y/n): ")
        if response.lower() == 'y':
            print("\n🌐 启动服务器...")
            print("访问: http://localhost:8000")
            print("按 Ctrl+C 停止服务器\n")
            time.sleep(2)
            os.chdir(backend_dir)
            os.system("python main.py")
    else:
        print("\n❌ 部分测试失败，请检查错误信息")
        print("查看详细日志:")
        print(f"  cd {backend_dir}")
        print("  pytest tests/ -v --tb=long")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 已取消")
        sys.exit(0)
