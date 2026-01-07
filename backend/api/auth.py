from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import time
import hmac
import hashlib
import os
import yaml
from pathlib import Path
from backend.services.monitoring_service import monitoring_service

router = APIRouter(prefix="/api/auth")


# 从配置文件加载权限配置
def load_auth_config():
    config_path = Path(__file__).parent.parent / "config" / "auth.yaml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        # 回退到默认配置
        print(f"Warning: Failed to load auth config: {e}, using defaults")
        return {
            "users": {
                "yeling": {"password": "yeling", "role": "superadmin"},
                "admin": {"password": "admin", "role": "admin"},
                "yangyang": {"password": "yangyang", "role": "user"},
            },
            "roles": {
                "superadmin": ["*"],
                "admin": ["view", "run", "maintain", "launch_dashboard"],
                "user": ["view", "launch_dashboard"],
            },
            "auth": {
                "secret": "ylai-secret",
                "token_expire_hours": 8,
                "allow_dev_token_in_query": True
            }
        }

auth_config = load_auth_config()

# 用户配置
USERS = auth_config.get("users", {})

# 角色到权限映射
ROLE_PERMS = {role: set(perms) for role, perms in auth_config.get("roles", {}).items()}

# 认证配置
AUTH_CONFIG = auth_config.get("auth", {})
SECRET = os.getenv("AUTH_SECRET", AUTH_CONFIG.get("secret", "ylai-secret"))
TOKEN_EXPIRE_HOURS = AUTH_CONFIG.get("token_expire_hours", 8)
ALLOW_DEV_TOKEN_IN_QUERY = AUTH_CONFIG.get("allow_dev_token_in_query", True)


class LoginPayload(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


def _sign(username: str, role: str, exp_s: int = 8 * 3600) -> str:
    ts = int(time.time())
    exp = ts + exp_s
    msg = f"{username}:{role}:{exp}"
    sig = hmac.new(SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return f"{msg}:{sig}"


def _verify(token: str) -> Optional[dict]:
    try:
        parts = token.split(":")
        if len(parts) != 4:
            return None
        username, role, exp_str, sig = parts
        msg = f"{username}:{role}:{int(exp_str)}"
        expected = hmac.new(SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        if int(exp_str) < int(time.time()):
            return None
        return {"username": username, "role": role, "exp": int(exp_str)}
    except Exception:
        return None


@router.post("/login")
def login(payload: LoginPayload) -> Token:
    start_time = time.time()
    try:
        user = USERS.get(payload.username)
        if not user or user.get("password") != payload.password:
            # 记录登录失败监控指标
            duration = time.time() - start_time
            monitoring_service.record_api_request("POST", "/api/auth/login", 401, duration)
            raise HTTPException(status_code=401, detail="invalid credentials")
        role = user.get("role")
        tok = _sign(payload.username, role)
        # 记录登录成功监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/auth/login", 200, duration)
        return Token(access_token=tok, role=role)
    except HTTPException:
        raise
    except Exception as e:
        # 记录登录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/auth/login", 500, duration)
        raise


def get_current(request: Request) -> dict:
    auth = request.headers.get("Authorization") or ""
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1]
        info = _verify(token)
        if info:
            return info
    # 允许在开发环境通过 query 传 token
    token = request.query_params.get("token")
    if token:
        info = _verify(token)
        if info:
            return info
    raise HTTPException(status_code=401, detail="unauthorized")


def require_role(*roles: str):
    async def _dep(info: dict = Depends(get_current)):
        role = info.get("role")
        if "superadmin" == role:
            return info
        if roles and role not in roles:
            raise HTTPException(status_code=403, detail="forbidden: role")
        return info
    return _dep


def require_perm(*perms: str):
    async def _dep(info: dict = Depends(get_current)):
        role = info.get("role")
        if role == "superadmin":
            return info
        granted = ROLE_PERMS.get(role, set())
        if "*" in granted:
            return info
        if not all(p in granted for p in perms):
            raise HTTPException(status_code=403, detail="forbidden: perm")
        return info
    return _dep


@router.get("/me")
def me(info: dict = Depends(get_current)):
    start_time = time.time()
    try:
        result = {"code": 0, "data": {"username": info.get("username"), "role": info.get("role"), "exp": info.get("exp")}}
        # 记录me端点监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("GET", "/api/auth/me", 200, duration)
        return result
    except Exception as e:
        # 记录me端点错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("GET", "/api/auth/me", 500, duration)
        raise
