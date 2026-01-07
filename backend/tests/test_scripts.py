"""
Script Unit Tests
"""
import pytest
from backend.core.registry import registry
from backend.scripts.phone_reverse import PhoneReverseScript
from backend.scripts.demo_run import DemoScript

class TestPhoneReverseScript:
    """号码逆向分析脚本测试"""

    def test_phone_reverse_initialization(self):
        """测试脚本初始化"""
        script = PhoneReverseScript()
        assert script.name == "phone_reverse"

    def test_phone_reverse_run_valid(self):
        """测试有效号码分析"""
        script = PhoneReverseScript()
        result = script.run(phone="13800138000")

        assert isinstance(result, dict)
        assert "status" in result
        assert "data" in result
        assert result["status"] == "success"
        assert "carrier" in result["data"]
        assert "province" in result["data"]
        assert "city" in result["data"]

    def test_phone_reverse_run_invalid(self):
        """测试无效号码"""
        script = PhoneReverseScript()

        # 测试空号码
        with pytest.raises(ValueError):
            script.run(phone="")

        # 测试非数字号码
        with pytest.raises(ValueError):
            script.run(phone="abcdefghijk")

        # 测试长度不正确的号码
        with pytest.raises(ValueError):
            script.run(phone="12345")

class TestDemoScript:
    """演示脚本测试"""

    def test_demo_initialization(self):
        """测试脚本初始化"""
        script = DemoScript()
        assert script.name == "demo_run"

    def test_demo_run_basic(self):
        """测试基本功能"""
        script = DemoScript()
        result = script.run(message="Hello World")

        assert isinstance(result, dict)
        assert result["echo"] == "Hello World"
        assert result["length"] == 11
        assert result["upper"] == "HELLO WORLD"
        assert result["lower"] == "hello world"

    def test_demo_run_empty_message(self):
        """测试空消息"""
        script = DemoScript()
        result = script.run(message="")

        assert result["echo"] == ""
        assert result["length"] == 0
        assert result["upper"] == ""
        assert result["lower"] == ""

    def test_demo_run_special_chars(self):
        """测试特殊字符"""
        script = DemoScript()
        message = "Hello@World#123"
        result = script.run(message=message)

        assert result["echo"] == message
        assert result["length"] == len(message)
        assert result["upper"] == message.upper()
        assert result["lower"] == message.lower()

class TestRegistry:
    """注册表测试"""

    def test_registry_has_scripts(self):
        """测试脚本注册"""
        assert "phone_reverse" in registry.scripts
        assert "demo_run" in registry.scripts

    def test_registry_get_script(self):
        """测试获取脚本"""
        phone_script = registry.get("phone_reverse")
        demo_script = registry.get("demo_run")

        assert phone_script is not None
        assert demo_script is not None
        assert isinstance(phone_script, PhoneReverseScript)
        assert isinstance(demo_script, DemoScript)

    def test_registry_get_nonexistent(self):
        """测试获取不存在的脚本"""
        script = registry.get("nonexistent")
        assert script is None