"""
Pytest配置 - 修复fixture警告
"""
import pytest

# 设置asyncio模式为auto，避免fixture警告
pytest_plugins = ('pytest_asyncio',)

def pytest_configure(config):
    """配置pytest"""
    config.option.asyncio_mode = "auto"
