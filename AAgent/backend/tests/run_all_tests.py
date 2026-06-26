"""
测试套件入口
运行所有测试
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


if __name__ == "__main__":
    # 运行所有测试
    exit_code = pytest.main([
        "tests/",
        "-v",
        "--tb=short",
        "--cov=services",
        "--cov=routes",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])
    
    sys.exit(exit_code)
