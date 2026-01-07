#!/usr/bin/env python3
"""
风控识别系统 - 风控类型分析模块
识别和分类不同的风控类型
"""

import asyncio
import re
import time
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from backend.core.base import BaseScript


class RiskAnalyzer(BaseScript):
    """风控类型分析器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 风控类型特征库
        self.risk_patterns = {
            'waf': {
                'cloudflare': [
                    r'cloudflare',
                    r'cf-browser-verification',
                    r'cf-challenge-running',
                    r'__cf_chl_jschl_tk__',
                    r'cf-ray',
                    r'cf-cache-status'
                ],
                'aliyun_waf': [
                    r'阿里云',
                    r'aliyun',
                    r'hws_host',
                    r'hws_visitor'
                ],
                'baidu_waf': [
                    r'百度云',
                    r'baidu',
                    r'yunjiasu'
                ],
                'tencent_waf': [
                    r'腾讯云',
                    r'tencent',
                    r'waf.tencent'
                ],
                'imperva': [
                    r'imperva',
                    r'incapsula'
                ],
                'akamai': [
                    r'akamai',
                    r'kona'
                ]
            },
            'captcha': {
                'recaptcha': [
                    r'recaptcha',
                    r'g-recaptcha',
                    r'google\.com/recaptcha',
                    r'recaptcha/api'
                ],
                'hcaptcha': [
                    r'hcaptcha',
                    r'hcaptcha\.com'
                ],
                'geetest': [
                    r'geetest',
                    r'gt\.js',
                    r'geetest\.com'
                ],
                'netease': [
                    r'netease',
                    r'易盾',
                    r'yidun'
                ],
                'tencent_captcha': [
                    r'tcaptcha',
                    r'腾讯防水墙'
                ]
            },
            'rate_limit': [
                r'rate limit',
                r'too many requests',
                r'request.*limit',
                r'429',
                r'frequency.*limit'
            ],
            'ip_block': [
                r'ip.*block',
                r'ip.*ban',
                r'forbidden',
                r'403',
                r'access.*deny'
            ],
            'user_agent_check': [
                r'user.?agent',
                r'browser.*check',
                r'device.*detect'
            ],
            'javascript_required': [
                r'javascript.*required',
                r'enable.*javascript',
                r'noscript'
            ],
            'bot_detection': [
                r'bot.*detect',
                r'automated.*request',
                r'suspicious.*activity'
            ]
        }

    async def run(self, page_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """执行风控类型分析"""
        try:
            self.logger.info("开始风控类型分析")

            # 预运行检查
            await self.pre_run()

            # 分析风控类型
            result = await self._analyze_risk_types(page_data, **kwargs)

            # 后运行处理
            await self.post_run(result)

            return result

        except Exception as e:
            await self.on_error(e)
            return {
                "status": "error",
                "error": str(e),
                "url": page_data.get('url', '')
            }

    async def _analyze_risk_types(self, page_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """分析风控类型"""
        url = page_data.get('url', '')
        html_content = page_data.get('content', '')
        page_info = page_data.get('page_info', {})
        features = page_data.get('features', {})

        # 综合分析
        analysis_result = {
            "url": url,
            "timestamp": time.time(),
            "risk_detected": False,
            "risk_types": [],
            "confidence_scores": {},
            "recommendations": [],
            "details": {}
        }

        # 1. 基于HTTP响应的分析
        http_analysis = self._analyze_http_response(page_info)
        analysis_result['details']['http'] = http_analysis

        # 2. 基于HTML内容的分析
        html_analysis = self._analyze_html_content(html_content)
        analysis_result['details']['html'] = html_analysis

        # 3. 基于页面特征的分析
        feature_analysis = self._analyze_page_features(features)
        analysis_result['details']['features'] = feature_analysis

        # 4. 基于行为的分析（预留）
        behavior_analysis = self._analyze_behavior_patterns(page_data)
        analysis_result['details']['behavior'] = behavior_analysis

        # 综合判断
        all_risk_types = set()
        all_risk_types.update(http_analysis.get('risk_types', []))
        all_risk_types.update(html_analysis.get('risk_types', []))
        all_risk_types.update(feature_analysis.get('risk_types', []))
        all_risk_types.update(behavior_analysis.get('risk_types', []))

        analysis_result['risk_types'] = list(all_risk_types)
        analysis_result['risk_detected'] = len(all_risk_types) > 0

        # 计算置信度
        analysis_result['confidence_scores'] = self._calculate_confidence_scores(
            http_analysis, html_analysis, feature_analysis, behavior_analysis
        )

        # 生成建议
        analysis_result['recommendations'] = self._generate_recommendations(
            analysis_result['risk_types'],
            analysis_result['confidence_scores']
        )

        analysis_result['status'] = 'success'
        return analysis_result

    def _analyze_http_response(self, page_info: Dict[str, Any]) -> Dict[str, Any]:
        """基于HTTP响应分析风控"""
        result = {
            "risk_types": [],
            "indicators": {},
            "confidence": 0.0
        }

        status_code = page_info.get('status_code', 200)
        headers = page_info.get('headers', {})
        response_time = page_info.get('response_time', 0)

        # 状态码分析
        if status_code == 403:
            result["risk_types"].append("ip_block")
            result["indicators"]["status_403"] = True
        elif status_code == 429:
            result["risk_types"].append("rate_limit")
            result["indicators"]["status_429"] = True
        elif status_code == 503:
            result["risk_types"].append("waf_block")
            result["indicators"]["status_503"] = True

        # 响应头分析
        server = headers.get('server', '').lower()
        if 'cloudflare' in server:
            result["risk_types"].append("waf_cloudflare")
            result["indicators"]["server_cloudflare"] = True
        elif 'aliyun' in server or 'alibaba' in server:
            result["risk_types"].append("waf_aliyun")
            result["indicators"]["server_aliyun"] = True

        # 检查特殊响应头
        cf_ray = headers.get('cf-ray')
        if cf_ray:
            result["risk_types"].append("waf_cloudflare")
            result["indicators"]["cf_ray_header"] = True

        # 响应时间分析（异常长的响应可能表示挑战）
        if response_time > 10:
            result["indicators"]["slow_response"] = True

        result["confidence"] = min(1.0, len(result["risk_types"]) * 0.3 + len(result["indicators"]) * 0.1)
        return result

    def _analyze_html_content(self, html_content: str) -> Dict[str, Any]:
        """基于HTML内容分析风控"""
        result = {
            "risk_types": [],
            "indicators": {},
            "confidence": 0.0
        }

        if not html_content:
            return result

        html_lower = html_content.lower()

        # 检查各种风控特征
        for category, patterns in self.risk_patterns.items():
            if category == 'waf':
                for waf_type, waf_patterns in patterns.items():
                    for pattern in waf_patterns:
                        if re.search(pattern, html_lower, re.IGNORECASE):
                            result["risk_types"].append(f"{category}_{waf_type}")
                            result["indicators"][f"{category}_{waf_type}"] = True
                            break
            elif category == 'captcha':
                for captcha_type, captcha_patterns in patterns.items():
                    for pattern in captcha_patterns:
                        if re.search(pattern, html_lower, re.IGNORECASE):
                            result["risk_types"].append(f"{category}_{captcha_type}")
                            result["indicators"][f"{category}_{captcha_type}"] = True
                            break
            else:
                # 其他类型的模式
                for pattern in patterns:
                    if re.search(pattern, html_lower, re.IGNORECASE):
                        result["risk_types"].append(category)
                        result["indicators"][category] = True
                        break

        # 检查JavaScript挑战
        if 'challenge-platform' in html_content or 'challenge' in html_content:
            result["risk_types"].append("javascript_challenge")
            result["indicators"]["js_challenge"] = True

        # 检查重定向到验证页面
        if 'verify' in html_content or 'captcha' in html_content:
            result["risk_types"].append("redirect_captcha")
            result["indicators"]["redirect_verify"] = True

        result["confidence"] = min(1.0, len(result["risk_types"]) * 0.4 + len(result["indicators"]) * 0.15)
        return result

    def _analyze_page_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """基于页面特征分析风控"""
        result = {
            "risk_types": [],
            "indicators": {},
            "confidence": 0.0
        }

        security_indicators = features.get('security_indicators', {})

        # 检查安全指标
        if security_indicators.get('has_cloudflare'):
            result["risk_types"].append("waf_cloudflare")
            result["indicators"]["cloudflare_detected"] = True

        if security_indicators.get('has_recaptcha'):
            result["risk_types"].append("captcha_recaptcha")
            result["indicators"]["recaptcha_detected"] = True

        if security_indicators.get('has_hcaptcha'):
            result["risk_types"].append("captcha_hcaptcha")
            result["indicators"]["hcaptcha_detected"] = True

        if security_indicators.get('has_403_forbidden'):
            result["risk_types"].append("ip_block")
            result["indicators"]["forbidden_content"] = True

        if security_indicators.get('has_429_too_many'):
            result["risk_types"].append("rate_limit")
            result["indicators"]["rate_limit_content"] = True

        # 分析DOM结构
        dom_structure = features.get('dom_structure', {})
        iframe_count = dom_structure.get('iframe_count', 0)
        if iframe_count > 3:
            result["risk_types"].append("iframe_challenge")
            result["indicators"]["multiple_iframes"] = True

        # 分析脚本
        scripts = features.get('scripts', {})
        script_count = scripts.get('count', 0)
        if script_count > 20:
            result["indicators"]["many_scripts"] = True

        result["confidence"] = min(1.0, len(result["risk_types"]) * 0.5 + len(result["indicators"]) * 0.2)
        return result

    def _analyze_behavior_patterns(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """基于行为模式分析风控（预留接口）"""
        return {
            "risk_types": [],
            "indicators": {},
            "confidence": 0.0
        }

    def _calculate_confidence_scores(self, *analyses) -> Dict[str, float]:
        """计算各类风控的置信度"""
        confidence_scores = {}

        # 收集所有检测到的风险类型
        all_types = set()
        for analysis in analyses:
            all_types.update(analysis.get('risk_types', []))

        # 为每个类型计算置信度
        for risk_type in all_types:
            scores = []
            for analysis in analyses:
                if risk_type in analysis.get('risk_types', []):
                    scores.append(analysis.get('confidence', 0.0))

            if scores:
                # 取平均值作为最终置信度
                confidence_scores[risk_type] = sum(scores) / len(scores)
            else:
                confidence_scores[risk_type] = 0.0

        return confidence_scores

    def _generate_recommendations(self, risk_types: List[str],
                                confidence_scores: Dict[str, float]) -> List[str]:
        """生成应对建议"""
        recommendations = []

        # 根据检测到的风险类型生成建议
        for risk_type in risk_types:
            confidence = confidence_scores.get(risk_type, 0.0)

            if confidence < 0.3:
                continue  # 置信度太低，跳过

            if 'waf' in risk_type:
                if 'cloudflare' in risk_type:
                    recommendations.extend([
                        "检测到Cloudflare WAF，建议使用住宅IP代理",
                        "启用JavaScript渲染模拟真实浏览器",
                        "调整请求频率，避免触发挑战"
                    ])
                elif 'aliyun' in risk_type:
                    recommendations.extend([
                        "检测到阿里云WAF，建议更换User-Agent",
                        "使用代理IP分散请求",
                        "启用请求头随机化"
                    ])
                else:
                    recommendations.append(f"检测到WAF ({risk_type})，建议启用高级反检测措施")

            elif 'captcha' in risk_type:
                if 'recaptcha' in risk_type:
                    recommendations.extend([
                        "检测到reCAPTCHA，建议集成2Captcha或类似服务",
                        "启用浏览器自动化解决验证码"
                    ])
                elif 'hcaptcha' in risk_type:
                    recommendations.extend([
                        "检测到hCaptcha，建议使用专用解决服务",
                        "准备备用验证码解决方案"
                    ])
                else:
                    recommendations.append(f"检测到验证码 ({risk_type})，建议集成验证码识别服务")

            elif risk_type == 'rate_limit':
                recommendations.extend([
                    "检测到频率限制，建议降低请求频率",
                    "启用请求队列和间隔控制",
                    "使用代理IP轮换"
                ])

            elif risk_type == 'ip_block':
                recommendations.extend([
                    "检测到IP封禁，建议立即更换代理IP",
                    "启用IP池轮换策略",
                    "检查请求头和行为模式"
                ])

            elif risk_type == 'javascript_required':
                recommendations.extend([
                    "检测到需要JavaScript，建议启用浏览器自动化",
                    "配置无头浏览器进行页面渲染"
                ])

        # 去重并排序
        recommendations = list(set(recommendations))
        return recommendations

    async def analyze_batch(self, pages_data: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """批量分析风控类型"""
        results = []
        for page_data in pages_data:
            result = await self.run(page_data, **kwargs)
            results.append(result)

        return results