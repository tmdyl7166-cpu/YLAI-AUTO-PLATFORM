"""
✅ AI增强爬虫脚本
功能：集成AI模型的智能网页数据爬取与逆向推理
"""
import asyncio
import aiohttp
import json
import re
import hashlib
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import time
import random

from backend.core.base import BaseScript
from backend.core.registry import registry
from backend.core.logger import logger
from backend.scripts.ai_coordinator import AIModelCoordinator


@registry.register("spider")
class SpiderScript(BaseScript):
    """AI增强网页爬虫脚本"""

    name = "spider"
    description = "AI增强智能爬虫"
    version = "2.0.0"

    def __init__(self):
        super().__init__()
        self.ai_coordinator = None
        self.session = None
        self.visited_urls = set()
        self.max_depth = 3
        self.max_pages = 50
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]

    async def pre_run(self, **kwargs):
        """初始化AI协调器和HTTP会话"""
        await super().pre_run(**kwargs)

        # 初始化AI协调器
        try:
            self.ai_coordinator = AIModelCoordinator()
            await self.ai_coordinator.initialize()
            logger.info("✅ AI协调器初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ AI协调器初始化失败: {e}")
            self.ai_coordinator = None

        # 初始化HTTP会话
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        执行AI增强爬虫任务
        参数:
            url (str): 目标网址
            depth (int): 爬取深度，默认3
            max_pages (int): 最大页面数，默认50
            ai_enhanced (bool): 是否启用AI增强，默认True
            target_data (str): 目标数据类型 ('content', 'structure', 'api', 'auto')
        返回:
            dict: 包含爬取结果和AI分析
        """
        url = kwargs.get("url", "https://example.com")
        depth = kwargs.get("depth", self.max_depth)
        max_pages = kwargs.get("max_pages", self.max_pages)
        ai_enhanced = kwargs.get("ai_enhanced", True)
        target_data = kwargs.get("target_data", "auto")

        logger.info(f"🕷️🤖 AI增强爬虫启动 - 目标: {url}")
        logger.info(f"🎯 目标数据类型: {target_data}, AI增强: {ai_enhanced}")

        try:
            results = {
                "status": "success",
                "url": url,
                "pages_crawled": 0,
                "data_collected": [],
                "ai_analysis": {},
                "reverse_engineering": {},
                "recommendations": []
            }

            # AI预分析：理解目标网站结构
            if ai_enhanced and self.ai_coordinator:
                pre_analysis = await self._ai_pre_analysis(url, target_data)
                results["ai_analysis"]["pre_analysis"] = pre_analysis

                # 根据AI分析调整爬取策略
                if pre_analysis.get("suggested_strategy"):
                    depth = pre_analysis["suggested_strategy"].get("depth", depth)
                    max_pages = pre_analysis["suggested_strategy"].get("max_pages", max_pages)
                    logger.info(f"📊 AI调整策略 - 深度:{depth}, 页面:{max_pages}")

            # 执行智能爬取
            crawl_results = await self._intelligent_crawl(url, depth, max_pages, target_data)
            results.update(crawl_results)

            # AI后分析：数据处理和逆向推理
            if ai_enhanced and self.ai_coordinator and results["data_collected"]:
                post_analysis = await self._ai_post_analysis(results["data_collected"], target_data)
                results["ai_analysis"]["post_analysis"] = post_analysis

                # 逆向工程分析
                reverse_analysis = await self._reverse_engineering_analysis(results["data_collected"])
                results["reverse_engineering"] = reverse_analysis

                # 生成优化建议
                recommendations = await self._generate_recommendations(results)
                results["recommendations"] = recommendations

            logger.info(f"✅ 爬取完成 - 页面:{results['pages_crawled']}, 数据项:{len(results['data_collected'])}")
            return results

        except Exception as e:
            logger.error(f"❌ 爬虫执行失败: {e}")
            return {"status": "failed", "error": str(e)}

    async def _ai_pre_analysis(self, url: str, target_data: str) -> Dict[str, Any]:
        """AI预分析：理解网站结构和制定爬取策略"""
        try:
            prompt = f"""
            分析目标网站: {url}
            目标数据类型: {target_data}

            请提供以下分析:
            1. 网站类型和主要内容
            2. 建议的爬取策略（深度、页面数、优先级）
            3. 潜在的数据结构和API端点
            4. 反爬虫机制识别
            5. 优化建议

            返回JSON格式。
            """

            analysis_result = await self.ai_coordinator.run('analyze_content', content=prompt)

            if analysis_result.get('status') == 'success':
                return analysis_result.get('result', {})
            else:
                logger.warning("AI预分析失败，使用默认策略")
                return {
                    "suggested_strategy": {"depth": 2, "max_pages": 20},
                    "content_type": "unknown",
                    "anti_crawler": "basic"
                }

        except Exception as e:
            logger.error(f"AI预分析异常: {e}")
            return {}

    async def _intelligent_crawl(self, start_url: str, depth: int, max_pages: int, target_data: str) -> Dict[str, Any]:
        """智能爬取算法"""
        results = {
            "pages_crawled": 0,
            "data_collected": [],
            "structure_analysis": {},
            "api_endpoints": []
        }

        queue = [(start_url, 0)]  # (url, depth)
        visited = set()

        while queue and results["pages_crawled"] < max_pages:
            current_url, current_depth = queue.pop(0)

            if current_url in visited or current_depth > depth:
                continue

            visited.add(current_url)
            results["pages_crawled"] += 1

            try:
                # 智能请求头选择
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }

                # 添加随机延迟避免被检测
                await asyncio.sleep(random.uniform(1, 3))

                async with self.session.get(current_url, headers=headers) as response:
                    if response.status != 200:
                        logger.warning(f"页面请求失败 {current_url}: {response.status}")
                        continue

                    content = await response.text()
                    content_type = response.headers.get('content-type', '')

                    # 根据目标数据类型处理内容
                    page_data = await self._process_page_content(
                        current_url, content, content_type, target_data
                    )

                    if page_data:
                        results["data_collected"].append(page_data)

                    # 智能链接提取和过滤
                    if current_depth < depth:
                        links = await self._extract_links_smart(content, current_url, target_data)
                        for link in links:
                            if link not in visited:
                                queue.append((link, current_depth + 1))

            except Exception as e:
                logger.error(f"爬取页面失败 {current_url}: {e}")
                continue

        return results

    async def _process_page_content(self, url: str, content: str, content_type: str, target_data: str) -> Optional[Dict[str, Any]]:
        """智能内容处理"""
        try:
            page_data = {
                "url": url,
                "content_type": content_type,
                "timestamp": time.time(),
                "size": len(content)
            }

            if 'text/html' in content_type:
                # HTML内容处理
                soup = BeautifulSoup(content, 'html.parser')

                # 提取标题
                title = soup.title.string if soup.title else ""
                page_data["title"] = title.strip() if title else ""

                # 提取主要内容
                main_content = self._extract_main_content(soup)
                page_data["content"] = main_content

                # 提取元数据
                meta_data = self._extract_meta_data(soup)
                page_data["meta"] = meta_data

                # 提取结构化数据
                structured_data = self._extract_structured_data(soup)
                page_data["structured_data"] = structured_data

            elif 'application/json' in content_type:
                # JSON API响应
                try:
                    json_data = json.loads(content)
                    page_data["json_data"] = json_data
                    page_data["api_type"] = "json"
                except:
                    page_data["raw_content"] = content[:1000]  # 限制大小

            else:
                # 其他类型内容
                page_data["raw_content"] = content[:2000] if len(content) > 2000 else content

            # 根据目标数据类型添加特定处理
            if target_data == "content":
                page_data["processed_content"] = await self._process_text_content(page_data)
            elif target_data == "structure":
                page_data["structure_analysis"] = await self._analyze_page_structure(page_data)
            elif target_data == "api":
                page_data["api_analysis"] = await self._analyze_api_structure(page_data)

            return page_data

        except Exception as e:
            logger.error(f"内容处理失败 {url}: {e}")
            return None

    async def _extract_links_smart(self, content: str, base_url: str, target_data: str) -> List[str]:
        """智能链接提取"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            links = []

            # 提取所有链接
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                absolute_url = urljoin(base_url, href)

                # 过滤条件
                parsed = urlparse(absolute_url)
                if (parsed.scheme in ['http', 'https'] and
                    parsed.netloc and
                    absolute_url not in self.visited_urls):

                    # 根据目标数据类型过滤链接
                    if target_data == "content" and self._is_content_page(absolute_url, a_tag):
                        links.append(absolute_url)
                    elif target_data == "api" and self._is_api_endpoint(absolute_url):
                        links.append(absolute_url)
                    elif target_data == "auto":
                        links.append(absolute_url)

            # 限制链接数量，避免过度爬取
            return links[:10]  # 每个页面最多10个链接

        except Exception as e:
            logger.error(f"链接提取失败: {e}")
            return []

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """提取主要内容"""
        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()

        # 尝试找到主要内容区域
        content_selectors = [
            'main', 'article', '.content', '#content',
            '.main-content', '.post-content', '.entry-content'
        ]

        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                return content_elem.get_text(strip=True)

        # 默认提取body内容
        body = soup.body
        return body.get_text(strip=True) if body else ""

    def _extract_meta_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取元数据"""
        meta = {}

        # 提取meta标签
        for meta_tag in soup.find_all('meta'):
            name = meta_tag.get('name') or meta_tag.get('property')
            content = meta_tag.get('content')
            if name and content:
                meta[name] = content

        # 提取Open Graph数据
        og_data = {}
        for og_tag in soup.find_all('meta', property=re.compile(r'^og:')):
            og_data[og_tag['property']] = og_tag.get('content', '')

        meta['open_graph'] = og_data

        return meta

    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取结构化数据"""
        structured_data = {}

        # 提取JSON-LD数据
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    structured_data['json_ld'] = data
                else:
                    structured_data.setdefault('json_ld', []).append(data)
            except:
                continue

        # 提取微数据
        microdata = []
        for item in soup.find_all(attrs={'itemtype': True}):
            item_data = {
                'type': item.get('itemtype'),
                'properties': {}
            }
            for prop in item.find_all(attrs={'itemprop': True}):
                item_data['properties'][prop.get('itemprop')] = prop.get_text(strip=True)
            microdata.append(item_data)

        structured_data['microdata'] = microdata

        return structured_data

    def _is_content_page(self, url: str, a_tag) -> bool:
        """判断是否为内容页面"""
        text = a_tag.get_text(strip=True).lower()
        href = url.lower()

        # 内容页面特征
        content_keywords = ['文章', '新闻', '博客', 'post', 'article', 'news', 'blog']
        skip_keywords = ['登录', '注册', '广告', 'about', 'contact', 'privacy']

        return (any(keyword in text or keyword in href for keyword in content_keywords) and
                not any(keyword in text or keyword in href for keyword in skip_keywords))

    def _is_api_endpoint(self, url: str) -> bool:
        """判断是否为API端点"""
        parsed = urlparse(url)
        path = parsed.path.lower()

        # API特征
        api_patterns = ['/api/', '/v1/', '/v2/', '/rest/', '/graphql']

        return any(pattern in path for pattern in api_patterns)

    async def _process_text_content(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI处理文本内容"""
        if not self.ai_coordinator:
            return {"summary": "AI未启用"}

        try:
            content = page_data.get("content", "")
            if not content:
                return {"summary": "无内容"}

            prompt = f"请分析以下网页内容，提取关键信息：\n\n{content[:2000]}"

            result = await self.ai_coordinator.run('analyze_content', content=prompt)

            if result.get('status') == 'success':
                return result.get('result', {})
            else:
                return {"summary": "AI分析失败"}

        except Exception as e:
            logger.error(f"文本内容处理失败: {e}")
            return {"error": str(e)}

    async def _analyze_page_structure(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI分析页面结构"""
        if not self.ai_coordinator:
            return {"structure": "AI未启用"}

        try:
            # 使用AI分析页面结构
            structure_info = {
                "url": page_data.get("url"),
                "title": page_data.get("title"),
                "has_structured_data": bool(page_data.get("structured_data")),
                "content_length": len(page_data.get("content", ""))
            }

            prompt = f"分析页面结构：{json.dumps(structure_info, ensure_ascii=False)}"

            result = await self.ai_coordinator.run('analyze_content', content=prompt)

            if result.get('status') == 'success':
                return result.get('result', {})
            else:
                return {"structure": "AI分析失败"}

        except Exception as e:
            logger.error(f"页面结构分析失败: {e}")
            return {"error": str(e)}

    async def _analyze_api_structure(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI分析API结构"""
        if not self.ai_coordinator:
            return {"api": "AI未启用"}

        try:
            json_data = page_data.get("json_data")
            if not json_data:
                return {"api": "非API响应"}

            prompt = f"分析API响应结构：\n{json.dumps(json_data, ensure_ascii=False, indent=2)[:2000]}"

            result = await self.ai_coordinator.run('analyze_content', content=prompt)

            if result.get('status') == 'success':
                return result.get('result', {})
            else:
                return {"api": "AI分析失败"}

        except Exception as e:
            logger.error(f"API结构分析失败: {e}")
            return {"error": str(e)}

    async def _ai_post_analysis(self, data_collected: List[Dict], target_data: str) -> Dict[str, Any]:
        """AI后分析：数据汇总和洞察"""
        if not self.ai_coordinator:
            return {"analysis": "AI未启用"}

        try:
            # 数据汇总
            summary = {
                "total_pages": len(data_collected),
                "content_types": {},
                "data_quality": {},
                "patterns": []
            }

            for item in data_collected:
                content_type = item.get("content_type", "unknown")
                summary["content_types"][content_type] = summary["content_types"].get(content_type, 0) + 1

            # AI深度分析
            analysis_prompt = f"""
            分析爬取数据汇总：
            - 总页面数: {summary['total_pages']}
            - 内容类型分布: {summary['content_types']}
            - 目标数据类型: {target_data}

            请提供：
            1. 数据质量评估
            2. 发现的模式和趋势
            3. 潜在的价值洞察
            4. 进一步分析建议
            """

            result = await self.ai_coordinator.run('complex_reasoning', content=analysis_prompt)

            if result.get('status') == 'success':
                summary.update(result.get('result', {}))
                return summary
            else:
                return {"analysis": "AI分析失败", "basic_stats": summary}

        except Exception as e:
            logger.error(f"AI后分析失败: {e}")
            return {"error": str(e)}

    async def _reverse_engineering_analysis(self, data_collected: List[Dict]) -> Dict[str, Any]:
        """逆向工程分析"""
        if not self.ai_coordinator:
            return {"reverse_engineering": "AI未启用"}

        try:
            analysis = {
                "patterns_discovered": [],
                "potential_apis": [],
                "data_structures": [],
                "security_insights": [],
                "optimization_opportunities": []
            }

            # 分析数据模式
            for item in data_collected:
                if item.get("structured_data"):
                    analysis["data_structures"].append({
                        "url": item["url"],
                        "structures": list(item["structured_data"].keys())
                    })

                # 查找API模式
                if "api" in item.get("url", "").lower():
                    analysis["potential_apis"].append(item["url"])

            # AI逆向推理
            reverse_prompt = f"""
            基于以下数据进行逆向工程分析：
            数据结构: {analysis['data_structures'][:5]}
            潜在API: {analysis['potential_apis'][:5]}

            请推断：
            1. 系统架构模式
            2. 数据流向
            3. 潜在的安全漏洞
            4. 性能优化点
            5. 扩展可能性
            """

            result = await self.ai_coordinator.run('complex_reasoning', content=reverse_prompt)

            if result.get('status') == 'success':
                analysis.update(result.get('result', {}))
                return analysis
            else:
                return {"basic_analysis": analysis}

        except Exception as e:
            logger.error(f"逆向工程分析失败: {e}")
            return {"error": str(e)}

    async def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        if not self.ai_coordinator:
            return ["启用AI功能以获得更详细的建议"]

        try:
            context = {
                "pages_crawled": results.get("pages_crawled", 0),
                "data_types": list(set(item.get("content_type", "unknown") for item in results.get("data_collected", []))),
                "ai_analysis": bool(results.get("ai_analysis")),
                "reverse_engineering": bool(results.get("reverse_engineering"))
            }

            prompt = f"""
            基于爬虫执行结果生成优化建议：
            {json.dumps(context, ensure_ascii=False, indent=2)}

            请提供具体的改进建议，包括：
            1. 爬取策略优化
            2. 数据处理改进
            3. AI功能增强
            4. 性能优化
            5. 扩展建议
            """

            result = await self.ai_coordinator.run('task_planning', content=prompt)

            if result.get('status') == 'success':
                recommendations = result.get('result', {}).get('recommendations', [])
                return recommendations if isinstance(recommendations, list) else [str(recommendations)]
            else:
                return ["AI建议生成失败，请检查AI协调器状态"]

        except Exception as e:
            logger.error(f"生成建议失败: {e}")
            return [f"建议生成异常: {str(e)}"]

    async def post_run(self, result: Dict[str, Any]) -> None:
        """清理资源"""
        await super().post_run(result)

        if self.session:
            await self.session.close()

        if self.ai_coordinator:
            # 可选：清理AI协调器资源
            pass

    async def on_error(self, error: Exception) -> None:
        """错误处理"""
        await super().on_error(error)

        if self.session:
            await self.session.close()
