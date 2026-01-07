"""
风控检测器 - 自动识别风控类型
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class RiskType(Enum):
    NONE = "none"
    CAPTCHA = "captcha"
    RATE_LIMIT = "rate_limit"
    IP_BLOCK = "ip_block"
    ACCOUNT_BLOCK = "account_block"
    JS_CHALLENGE = "js_challenge"
    BOT_DETECTION = "bot_detection"
    UNKNOWN = "unknown"

class RiskDetector:
    """风控类型检测器"""

    def __init__(self):
        self.captcha_patterns = [
            r'captcha',
            r'verify.*code',
            r'请输入验证码',
            r'验证码',
            r'recaptcha',
            r'hcaptcha',
            r'geetest',
            r'滑动验证'
        ]

        self.rate_limit_patterns = [
            r'too.*many.*requests',
            r'rate.*limit',
            r'频率限制',
            r'请求过于频繁',
            r'429',
            r'slow.*down'
        ]

        self.ip_block_patterns = [
            r'ip.*block',
            r'ip.*ban',
            r'blocked.*ip',
            r'ip地址被封',
            r'403',
            r'access.*denied'
        ]

        self.account_block_patterns = [
            r'account.*block',
            r'account.*ban',
            r'账户被封',
            r'账户异常',
            r'login.*fail'
        ]

        self.js_challenge_patterns = [
            r'challenge',
            r'javascript.*required',
            r'js.*challenge',
            r'anti.*bot',
            r'cloudflare',
            r'ddos.*protection'
        ]

    def detect_risk_type(self, html: str, headers: Dict[str, Any] = None,
                         status_code: int = 200) -> Tuple[RiskType, Dict[str, Any]]:
        """
        检测风控类型

        Args:
            html: 页面HTML内容
            headers: 响应头
            status_code: HTTP状态码

        Returns:
            (风控类型, 详细信息)
        """
        html_lower = html.lower() if html else ""
        headers = headers or {}

        # 检查状态码
        if status_code == 429:
            return RiskType.RATE_LIMIT, {"reason": "HTTP 429 Too Many Requests"}
        elif status_code == 403:
            return RiskType.IP_BLOCK, {"reason": "HTTP 403 Forbidden"}
        elif status_code == 503:
            return RiskType.JS_CHALLENGE, {"reason": "HTTP 503 Service Unavailable"}

        # 检查验证码
        for pattern in self.captcha_patterns:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return RiskType.CAPTCHA, {
                    "pattern": pattern,
                    "confidence": 0.9
                }

        # 检查频率限制
        for pattern in self.rate_limit_patterns:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return RiskType.RATE_LIMIT, {
                    "pattern": pattern,
                    "confidence": 0.8
                }

        # 检查IP封禁
        for pattern in self.ip_block_patterns:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return RiskType.IP_BLOCK, {
                    "pattern": pattern,
                    "confidence": 0.8
                }

        # 检查账户封禁
        for pattern in self.account_block_patterns:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return RiskType.ACCOUNT_BLOCK, {
                    "pattern": pattern,
                    "confidence": 0.7
                }

        # 检查JS挑战
        for pattern in self.js_challenge_patterns:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return RiskType.JS_CHALLENGE, {
                    "pattern": pattern,
                    "confidence": 0.8
                }

        # 检查响应头
        server = headers.get('server', '').lower()
        if 'cloudflare' in server:
            return RiskType.JS_CHALLENGE, {
                "server": server,
                "confidence": 0.9
            }

        # 检查是否包含反爬虫特征
        bot_detection_indicators = [
            'robot', 'bot', 'crawler', 'spider',
            'automated', 'suspicious', 'unusual'
        ]

        for indicator in bot_detection_indicators:
            if indicator in html_lower:
                return RiskType.BOT_DETECTION, {
                    "indicator": indicator,
                    "confidence": 0.6
                }

        return RiskType.NONE, {"confidence": 1.0}

    def analyze_response(self, response: Any) -> Dict[str, Any]:
        """
        分析HTTP响应，提取风控信息

        Args:
            response: HTTP响应对象

        Returns:
            分析结果
        """
        try:
            html = getattr(response, 'text', '') or getattr(response, 'content', '')
            headers = getattr(response, 'headers', {})
            status_code = getattr(response, 'status_code', 200)

            risk_type, details = self.detect_risk_type(html, headers, status_code)

            return {
                "risk_type": risk_type.value,
                "detected": risk_type != RiskType.NONE,
                "details": details,
                "status_code": status_code,
                "response_size": len(html) if html else 0
            }

        except Exception as e:
            logger.error(f"分析响应失败: {e}")
            return {
                "risk_type": RiskType.UNKNOWN.value,
                "detected": True,
                "details": {"error": str(e)},
                "status_code": 0,
                "response_size": 0
            }