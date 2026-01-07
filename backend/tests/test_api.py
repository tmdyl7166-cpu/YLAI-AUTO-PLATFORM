"""
API Integration Tests
"""
import pytest
from fastapi.testclient import TestClient
from backend.app import app
import os

# 设置测试环境
os.environ["ENV"] = "test"

client = TestClient(app)

class TestAuthAPI:
    """认证API测试"""

    def test_login_success(self):
        """测试成功登录"""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["role"] == "admin"

    def test_login_invalid_credentials(self):
        """测试无效凭据登录"""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "wrong"
        })
        assert response.status_code == 401

class TestPhoneAPI:
    """号码分析API测试"""

    def test_phone_analyze_without_auth(self):
        """测试无认证访问"""
        response = client.post("/api/phone/analyze", json={
            "phone": "13800138000"
        })
        assert response.status_code == 401

    def test_phone_analyze_invalid_format(self):
        """测试无效号码格式"""
        # 先登录获取token
        login_response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin"
        })
        token = login_response.json()["access_token"]

        response = client.post("/api/phone/analyze",
            json={"phone": "invalid"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400

    def test_phone_analyze_success(self):
        """测试成功号码分析"""
        # 先登录获取token
        login_response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin"
        })
        token = login_response.json()["access_token"]

        response = client.post("/api/phone/analyze",
            json={"phone": "13800138000"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "data" in data

class TestDemoAPI:
    """演示API测试"""

    def test_demo_run_success(self):
        """测试演示功能"""
        # 先登录获取token
        login_response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin"
        })
        token = login_response.json()["access_token"]

        response = client.post("/api/demo/run",
            json={"message": "test message"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "echo" in data
        assert "length" in data
        assert "upper" in data
        assert "lower" in data

class TestHealthAPI:
    """健康检查API测试"""

    def test_health_check(self):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "status" in data["data"]
        assert data["data"]["status"] == "ok"