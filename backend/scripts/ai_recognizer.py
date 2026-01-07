#!/usr/bin/env python3
"""
AI识别接口
提供图像识别、文本分析等AI推理服务
"""

import asyncio
import base64
import json
import time
import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import logging

from backend.core.base import BaseScript
from backend.services.ai_service import AIService


class AIRecognizer(BaseScript):
    """AI识别器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # AI服务
        self.ai_service = AIService()

        # OCR配置
        self.config = {
            'ddddocr_enabled': True,
            'opencv_enabled': True,
            'text_analysis_enabled': True,
            'image_preprocessing': True,
            'confidence_threshold': 0.8,
            'max_image_size': 1024 * 1024,  # 1MB
            'supported_formats': ['png', 'jpg', 'jpeg', 'bmp', 'webp'],
            'batch_processing': True,
            'cache_results': True
        }

        # OCR引擎
        self.ddddocr = None
        self._init_ocr()

        # 统计信息
        self.stats = {
            'total_recognitions': 0,
            'successful_recognitions': 0,
            'failed_recognitions': 0,
            'avg_processing_time': 0.0,
            'recognition_types': {},
            'cache_hits': 0,
            'cache_misses': 0
        }

        # 缓存
        self.cache: Dict[str, Dict[str, Any]] = {}

    def _init_ocr(self):
        """初始化OCR引擎"""
        try:
            if self.config['ddddocr_enabled']:
                import ddddocr
                self.ddddocr = ddddocr.DdddOcr()
                self.logger.info("ddddocr OCR引擎初始化成功")
        except ImportError:
            self.logger.warning("ddddocr未安装，将使用备用方法")
            self.ddddocr = None

    async def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """执行AI识别操作"""
        try:
            self.logger.info(f"执行AI识别操作: {action}")

            # 预运行检查
            await self.pre_run()

            # 执行操作
            if action == 'recognize_captcha':
                result = await self._recognize_captcha(**kwargs)
            elif action == 'analyze_text':
                result = await self._analyze_text(**kwargs)
            elif action == 'classify_content':
                result = await self._classify_content(**kwargs)
            elif action == 'extract_entities':
                result = await self._extract_entities(**kwargs)
            elif action == 'sentiment_analysis':
                result = await self._sentiment_analysis(**kwargs)
            elif action == 'batch_recognize':
                result = await self._batch_recognize(**kwargs)
            else:
                result = {"status": "error", "error": f"未知操作: {action}"}

            # 后运行处理
            await self.post_run(result)

            return result

        except Exception as e:
            await self.on_error(e)
            return {
                "status": "error",
                "error": str(e)
            }

    async def _recognize_captcha(self, image_path: str = None, image_data: bytes = None,
                               image_base64: str = None, **kwargs) -> Dict[str, Any]:
        """识别验证码"""
        start_time = time.time()

        try:
            # 获取图像数据
            image_bytes = await self._get_image_data(image_path, image_data, image_base64)
            if not image_bytes:
                return {"status": "error", "error": "无法获取图像数据"}

            # 缓存检查
            cache_key = self._get_image_cache_key(image_bytes)
            if self.config['cache_results'] and cache_key in self.cache:
                cached_result = self.cache[cache_key]
                if time.time() - cached_result['timestamp'] < 3600:  # 1小时缓存
                    self.stats['cache_hits'] += 1
                    return {
                        "status": "success",
                        "text": cached_result['text'],
                        "confidence": cached_result['confidence'],
                        "cached": True,
                        "processing_time": time.time() - start_time
                    }

            self.stats['cache_misses'] += 1

            # 图像预处理
            if self.config['image_preprocessing']:
                image_bytes = self._preprocess_image(image_bytes)

            # OCR识别
            text, confidence = await self._perform_ocr(image_bytes)

            processing_time = time.time() - start_time

            # 更新统计
            self._update_stats('captcha', processing_time, confidence > self.config['confidence_threshold'])

            # 缓存结果
            if self.config['cache_results']:
                self.cache[cache_key] = {
                    'text': text,
                    'confidence': confidence,
                    'timestamp': time.time()
                }

            return {
                "status": "success",
                "text": text,
                "confidence": confidence,
                "processing_time": round(processing_time, 3),
                "cached": False
            }

        except Exception as e:
            processing_time = time.time() - start_time
            self._update_stats('captcha', processing_time, False)
            self.logger.error(f"验证码识别失败: {e}")
            return {
                "status": "error",
                "error": f"验证码识别失败: {e}",
                "processing_time": round(processing_time, 3)
            }

    async def _analyze_text(self, text: str, analysis_type: str = 'general',
                          **kwargs) -> Dict[str, Any]:
        """分析文本"""
        start_time = time.time()

        try:
            if not text or len(text.strip()) == 0:
                return {"status": "error", "error": "文本不能为空"}

            # 构建分析提示
            prompts = {
                'general': f"请分析以下文本的主要内容、情感倾向和关键信息：\n\n{text}",
                'sentiment': f"请分析以下文本的情感倾向（积极/消极/中性），并给出置信度：\n\n{text}",
                'keywords': f"请提取以下文本的关键字和主题词：\n\n{text}",
                'summary': f"请为以下文本生成一个简洁的摘要：\n\n{text}"
            }

            prompt = prompts.get(analysis_type, prompts['general'])

            # 调用AI服务
            result = await self.ai_service.run('generate',
                prompt=prompt,
                temperature=0.3,
                max_tokens=256
            )

            processing_time = time.time() - start_time

            if result['status'] == 'success':
                self._update_stats('text_analysis', processing_time, True)
                return {
                    "status": "success",
                    "analysis": result['text'],
                    "analysis_type": analysis_type,
                    "processing_time": round(processing_time, 3)
                }
            else:
                self._update_stats('text_analysis', processing_time, False)
                return result

        except Exception as e:
            processing_time = time.time() - start_time
            self._update_stats('text_analysis', processing_time, False)
            self.logger.error(f"文本分析失败: {e}")
            return {
                "status": "error",
                "error": f"文本分析失败: {e}",
                "processing_time": round(processing_time, 3)
            }

    async def _classify_content(self, content: str, categories: List[str] = None,
                              **kwargs) -> Dict[str, Any]:
        """内容分类"""
        try:
            if not content:
                return {"status": "error", "error": "内容不能为空"}

            default_categories = ['新闻', '广告', '技术', '娱乐', '体育', '财经', '其他']
            categories = categories or default_categories

            prompt = f"""请将以下内容分类到最合适的类别中：

可用类别: {', '.join(categories)}

内容:
{content}

请只返回类别名称，不要其他解释。"""

            result = await self.ai_service.run('generate',
                prompt=prompt,
                temperature=0.1,  # 降低随机性，提高一致性
                max_tokens=50
            )

            if result['status'] == 'success':
                predicted_category = result['text'].strip()
                # 确保预测的类别在可用类别中
                if predicted_category not in categories:
                    predicted_category = '其他'

                return {
                    "status": "success",
                    "content": content[:100] + "..." if len(content) > 100 else content,
                    "predicted_category": predicted_category,
                    "available_categories": categories,
                    "confidence": 0.8  # 简化的置信度
                }
            else:
                return result

        except Exception as e:
            self.logger.error(f"内容分类失败: {e}")
            return {"status": "error", "error": f"内容分类失败: {e}"}

    async def _extract_entities(self, text: str, entity_types: List[str] = None,
                              **kwargs) -> Dict[str, Any]:
        """实体提取"""
        try:
            if not text:
                return {"status": "error", "error": "文本不能为空"}

            default_types = ['人名', '地名', '组织', '时间', '数字', 'URL']
            entity_types = entity_types or default_types

            prompt = f"""请从以下文本中提取指定类型的实体：

实体类型: {', '.join(entity_types)}

文本:
{text}

请以JSON格式返回结果，格式如下：
{{
    "entities": [
        {{"type": "人名", "value": "张三", "start": 10, "end": 12}},
        ...
    ]
}}"""

            result = await self.ai_service.run('generate',
                prompt=prompt,
                temperature=0.2,
                max_tokens=512
            )

            if result['status'] == 'success':
                try:
                    # 尝试解析JSON响应
                    entities_data = json.loads(result['text'])
                    entities = entities_data.get('entities', [])

                    return {
                        "status": "success",
                        "text": text,
                        "entities": entities,
                        "entity_types": entity_types
                    }
                except json.JSONDecodeError:
                    # 如果JSON解析失败，返回原始文本
                    return {
                        "status": "success",
                        "text": text,
                        "entities": [],
                        "raw_response": result['text'],
                        "parse_error": "JSON解析失败"
                    }
            else:
                return result

        except Exception as e:
            self.logger.error(f"实体提取失败: {e}")
            return {"status": "error", "error": f"实体提取失败: {e}"}

    async def _sentiment_analysis(self, text: str, **kwargs) -> Dict[str, Any]:
        """情感分析"""
        try:
            if not text:
                return {"status": "error", "error": "文本不能为空"}

            prompt = f"""请分析以下文本的情感倾向：

{text}

请返回JSON格式：
{{
    "sentiment": "positive|negative|neutral",
    "confidence": 0.85,
    "explanation": "简要解释"
}}"""

            result = await self.ai_service.run('generate',
                prompt=prompt,
                temperature=0.1,
                max_tokens=256
            )

            if result['status'] == 'success':
                try:
                    sentiment_data = json.loads(result['text'])
                    return {
                        "status": "success",
                        "text": text,
                        "sentiment": sentiment_data.get('sentiment', 'neutral'),
                        "confidence": sentiment_data.get('confidence', 0.5),
                        "explanation": sentiment_data.get('explanation', '')
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "success",
                        "text": text,
                        "sentiment": "neutral",
                        "confidence": 0.5,
                        "raw_response": result['text']
                    }
            else:
                return result

        except Exception as e:
            self.logger.error(f"情感分析失败: {e}")
            return {"status": "error", "error": f"情感分析失败: {e}"}

    async def _batch_recognize(self, items: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """批量识别"""
        results = []
        successful = 0
        failed = 0

        for item in items:
            if 'image_path' in item or 'image_data' in item or 'image_base64' in item:
                result = await self._recognize_captcha(**item)
            elif 'text' in item:
                result = await self._analyze_text(**item)
            else:
                result = {"status": "error", "error": "无效的项目数据"}

            results.append(result)

            if result['status'] == 'success':
                successful += 1
            else:
                failed += 1

        return {
            "status": "success",
            "total_items": len(items),
            "successful": successful,
            "failed": failed,
            "results": results
        }

    async def _get_image_data(self, image_path: str = None, image_data: bytes = None,
                            image_base64: str = None) -> Optional[bytes]:
        """获取图像数据"""
        try:
            if image_data:
                return image_data
            elif image_base64:
                return base64.b64decode(image_base64)
            elif image_path:
                path = Path(image_path)
                if path.exists() and path.stat().st_size <= self.config['max_image_size']:
                    return path.read_bytes()
                else:
                    self.logger.error(f"图像文件不存在或过大: {image_path}")
                    return None
            else:
                return None
        except Exception as e:
            self.logger.error(f"获取图像数据失败: {e}")
            return None

    def _preprocess_image(self, image_bytes: bytes) -> bytes:
        """图像预处理"""
        try:
            if not self.config['opencv_enabled']:
                return image_bytes

            # 转换为numpy数组
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                return image_bytes

            # 灰度化
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 二值化
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # 降噪
            denoised = cv2.medianBlur(binary, 3)

            # 编码回bytes
            success, encoded_img = cv2.imencode('.png', denoised)
            if success:
                return encoded_img.tobytes()
            else:
                return image_bytes

        except Exception as e:
            self.logger.warning(f"图像预处理失败: {e}")
            return image_bytes

    async def _perform_ocr(self, image_bytes: bytes) -> tuple[str, float]:
        """执行OCR识别"""
        try:
            if self.ddddocr:
                # 使用ddddocr进行识别
                result = self.ddddocr.classification(image_bytes)
                confidence = 0.9  # ddddocr不提供置信度，这里给个默认值
                return result, confidence
            else:
                # 备用方法：返回占位符
                return "识别失败：OCR引擎未初始化", 0.0

        except Exception as e:
            self.logger.error(f"OCR识别失败: {e}")
            return "OCR识别错误", 0.0

    def _get_image_cache_key(self, image_bytes: bytes) -> str:
        """生成图像缓存键"""
        import hashlib
        return hashlib.md5(image_bytes).hexdigest()

    def _update_stats(self, recognition_type: str, processing_time: float, success: bool):
        """更新统计信息"""
        self.stats['total_recognitions'] += 1

        if success:
            self.stats['successful_recognitions'] += 1
        else:
            self.stats['failed_recognitions'] += 1

        # 更新平均处理时间
        self.stats['avg_processing_time'] = (
            (self.stats['avg_processing_time'] * (self.stats['total_recognitions'] - 1)) +
            processing_time
        ) / self.stats['total_recognitions']

        # 更新识别类型统计
        if recognition_type not in self.stats['recognition_types']:
            self.stats['recognition_types'][recognition_type] = 0
        self.stats['recognition_types'][recognition_type] += 1

    async def close(self):
        """关闭识别器"""
        await self.ai_service.close()