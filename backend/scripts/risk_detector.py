#!/usr/bin/env python3
"""
风控识别系统 - 页面采集模块
负责采集目标网站的页面源码和特征提取
"""

import asyncio
import time
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, urljoin

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import re

from backend.core.base import BaseScript


class PageCollector(BaseScript):
    """页面采集器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ua = UserAgent()
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """创建带重试机制的会话"""
        session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
            raise_on_status=False
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    async def run(self, url: str, **kwargs) -> Dict[str, Any]:
        """执行页面采集"""
        try:
            self.logger.info(f"开始采集页面: {url}")

            # 预运行检查
            await self.pre_run()

            # 采集页面
            result = await self._collect_page(url, **kwargs)

            # 后运行处理
            await self.post_run()

            return result

        except Exception as e:
            await self.on_error(e)
            return {
                "status": "error",
                "error": str(e),
                "url": url
            }

    async def _collect_page(self, url: str, timeout: int = 30,
                          use_proxy: bool = False, **kwargs) -> Dict[str, Any]:
        """采集页面内容"""

        # 准备请求头
        headers = self._prepare_headers(url)

        # 准备代理（如果启用）
        proxies = None
        if use_proxy:
            proxies = await self._get_proxy()

        try:
            # 发送请求
            start_time = time.time()
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.session.get(
                    url,
                    headers=headers,
                    proxies=proxies,
                    timeout=timeout,
                    allow_redirects=True
                )
            )
            response_time = time.time() - start_time

            # 分析响应
            page_info = self._analyze_response(response, response_time)

            # 提取特征
            features = self._extract_features(response.text, url)

            return {
                "status": "success",
                "url": url,
                "page_info": page_info,
                "features": features,
                "content": response.text[:5000] if len(response.text) > 5000 else response.text  # 限制内容长度
            }

        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求失败: {url} - {e}")
            return {
                "status": "error",
                "error": f"请求失败: {str(e)}",
                "url": url
            }

    def _prepare_headers(self, url: str) -> Dict[str, str]:
        """准备请求头"""
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        # 根据域名调整Referer
        parsed_url = urlparse(url)
        if parsed_url.netloc:
            headers['Referer'] = f"{parsed_url.scheme}://{parsed_url.netloc}/"

        return headers

    async def _get_proxy(self) -> Optional[Dict[str, str]]:
        """获取代理（预留接口）"""
        # TODO: 集成代理池系统
        return None

    def _analyze_response(self, response: requests.Response, response_time: float) -> Dict[str, Any]:
        """分析HTTP响应"""
        return {
            "status_code": response.status_code,
            "response_time": round(response_time, 3),
            "content_length": len(response.content),
            "content_type": response.headers.get('content-type', ''),
            "server": response.headers.get('server', ''),
            "encoding": response.encoding,
            "final_url": response.url,
            "redirect_count": len(response.history),
            "headers": dict(response.headers)
        }

    def _extract_features(self, html_content: str, url: str) -> Dict[str, Any]:
        """提取页面特征"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')

            features = {
                "title": self._extract_title(soup),
                "meta_tags": self._extract_meta_tags(soup),
                "scripts": self._extract_scripts(soup),
                "forms": self._extract_forms(soup),
                "links": self._extract_links(soup, url),
                "images": self._extract_images(soup, url),
                "text_content": self._extract_text_content(soup),
                "dom_structure": self._analyze_dom_structure(soup),
                "security_indicators": self._check_security_indicators(html_content)
            }

            return features

        except Exception as e:
            self.logger.error(f"特征提取失败: {e}")
            return {"error": str(e)}

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取页面标题"""
        title_tag = soup.find('title')
        return title_tag.text.strip() if title_tag else ""

    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict[str, str]:
        """提取meta标签"""
        meta_tags = {}
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property') or meta.get('http-equiv')
            content = meta.get('content', '')
            if name:
                meta_tags[name.lower()] = content
        return meta_tags

    def _extract_scripts(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取脚本信息"""
        scripts = []
        for script in soup.find_all('script'):
            script_info = {
                "src": script.get('src', ''),
                "type": script.get('type', 'text/javascript'),
                "content_length": len(script.text) if script.text else 0
            }
            scripts.append(script_info)

        return {
            "count": len(scripts),
            "external": len([s for s in scripts if s['src']]),
            "inline": len([s for s in scripts if not s['src']]),
            "scripts": scripts[:10]  # 限制数量
        }

    def _extract_forms(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取表单信息"""
        forms = []
        for form in soup.find_all('form'):
            form_info = {
                "action": form.get('action', ''),
                "method": form.get('method', 'GET'),
                "inputs": len(form.find_all('input')),
                "textareas": len(form.find_all('textarea')),
                "selects": len(form.find_all('select'))
            }
            forms.append(form_info)

        return {
            "count": len(forms),
            "forms": forms
        }

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """提取链接信息"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                links.append({
                    "url": full_url,
                    "text": link.text.strip(),
                    "title": link.get('title', '')
                })

        return {
            "count": len(links),
            "internal": len([l for l in links if urlparse(l['url']).netloc == urlparse(base_url).netloc]),
            "external": len([l for l in links if urlparse(l['url']).netloc != urlparse(base_url).netloc]),
            "links": links[:20]  # 限制数量
        }

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """提取图片信息"""
        images = []
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src:
                full_url = urljoin(base_url, src)
                images.append({
                    "url": full_url,
                    "alt": img.get('alt', ''),
                    "title": img.get('title', '')
                })

        return {
            "count": len(images),
            "images": images[:10]  # 限制数量
        }

    def _extract_text_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取文本内容"""
        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        return {
            "total_length": len(text),
            "line_count": len(lines),
            "word_count": len(text.split()),
            "sample_text": text[:500]  # 样本文本
        }

    def _analyze_dom_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """分析DOM结构"""
        return {
            "total_tags": len(soup.find_all()),
            "div_count": len(soup.find_all('div')),
            "span_count": len(soup.find_all('span')),
            "p_count": len(soup.find_all('p')),
            "table_count": len(soup.find_all('table')),
            "iframe_count": len(soup.find_all('iframe')),
            "depth": self._calculate_dom_depth(soup)
        }

    def _calculate_dom_depth(self, soup: BeautifulSoup, max_depth: int = 10) -> int:
        """计算DOM最大深度"""
        def get_depth(element, current_depth=0):
            if current_depth >= max_depth:
                return max_depth
            if not element.findChildren():
                return current_depth
            return max(get_depth(child, current_depth + 1) for child in element.findChildren())

        return get_depth(soup)

    def _check_security_indicators(self, html_content: str) -> Dict[str, Any]:
        """检查安全指标"""
        indicators = {
            "has_captcha": bool(re.search(r'captcha|验证码|verification', html_content, re.I)),
            "has_cloudflare": bool(re.search(r'cloudflare|cf-browser-verification', html_content, re.I)),
            "has_recaptcha": bool(re.search(r'recaptcha|recaptcha/api', html_content, re.I)),
            "has_hcaptcha": bool(re.search(r'hcaptcha', html_content, re.I)),
            "has_403_forbidden": bool(re.search(r'403|forbidden|access denied', html_content, re.I)),
            "has_429_too_many": bool(re.search(r'429|too many requests', html_content, re.I)),
            "has_waf_detected": bool(re.search(r'waf|web application firewall', html_content, re.I))
        }

        return indicators