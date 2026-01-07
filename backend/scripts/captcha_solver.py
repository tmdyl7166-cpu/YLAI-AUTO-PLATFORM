#!/usr/bin/env python3
"""
风控识别系统 - 验证码识别模块
支持多种验证码类型的识别
"""

import asyncio
import base64
import time
from typing import Dict, Any, Optional, List
from io import BytesIO
from pathlib import Path

import ddddocr
import requests
from PIL import Image
import cv2
import numpy as np

from backend.core.base import BaseScript


class CaptchaSolver(BaseScript):
    """验证码识别器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ocr = ddddocr.DdddOcr()
        self.slide_ocr = ddddocr.DdddOcr(det=False, ocr=False)  # 滑动验证码专用
        self.detect_ocr = ddddocr.DdddOcr(det=True, ocr=False)  # 目标检测专用

        # 缓存配置
        self.cache_ttl = 300  # 5分钟缓存

    async def run(self, captcha_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """执行验证码识别"""
        try:
            self.logger.info("开始验证码识别")

            # 预运行检查
            await self.pre_run()

            # 识别验证码
            result = await self._solve_captcha(captcha_data, **kwargs)

            # 后运行处理
            await self.post_run()

            return result

        except Exception as e:
            await self.on_error(e)
            return {
                "status": "error",
                "error": str(e),
                "captcha_type": captcha_data.get('type', 'unknown')
            }

    async def _solve_captcha(self, captcha_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """识别验证码"""
        captcha_type = captcha_data.get('type', 'text')
        image_data = captcha_data.get('image')

        if not image_data:
            return {
                "status": "error",
                "error": "未提供验证码图片数据",
                "captcha_type": captcha_type
            }

        # 预处理图片
        processed_image = await self._preprocess_image(image_data)

        # 根据类型选择识别方法
        if captcha_type == 'text':
            result = await self._solve_text_captcha(processed_image)
        elif captcha_type == 'slide':
            result = await self._solve_slide_captcha(processed_image, captcha_data)
        elif captcha_type == 'click':
            result = await self._solve_click_captcha(processed_image, captcha_data)
        elif captcha_type == 'rotate':
            result = await self._solve_rotate_captcha(processed_image)
        else:
            result = await self._solve_generic_captcha(processed_image)

        # 添加识别统计
        result.update({
            "captcha_type": captcha_type,
            "processing_time": time.time(),
            "confidence": self._calculate_confidence(result)
        })

        return result

    async def _preprocess_image(self, image_data: Any) -> bytes:
        """预处理验证码图片"""
        try:
            # 处理不同格式的图片数据
            if isinstance(image_data, str):
                # Base64字符串
                if image_data.startswith('data:image'):
                    # 移除data URL前缀
                    image_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(image_data)
            elif isinstance(image_data, bytes):
                image_bytes = image_data
            elif hasattr(image_data, 'read'):
                # 文件对象
                image_bytes = image_data.read()
            else:
                raise ValueError(f"不支持的图片数据格式: {type(image_data)}")

            # 使用PIL进行基础处理
            image = Image.open(BytesIO(image_bytes))

            # 转换为RGB模式（如果需要）
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # 调整大小（如果太小）
            if image.size[0] < 50 or image.size[1] < 50:
                image = image.resize((max(100, image.size[0] * 2), max(100, image.size[1] * 2)), Image.LANCZOS)

            # 增强对比度
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)

            # 转换为bytes
            output = BytesIO()
            image.save(output, format='PNG')
            return output.getvalue()

        except Exception as e:
            self.logger.error(f"图片预处理失败: {e}")
            # 返回原始数据
            return image_data if isinstance(image_data, bytes) else image_data.encode()

    async def _solve_text_captcha(self, image_bytes: bytes) -> Dict[str, Any]:
        """识别文字验证码"""
        try:
            start_time = time.time()

            # 使用ddddocr识别
            result = self.ocr.classification(image_bytes)

            processing_time = time.time() - start_time

            return {
                "status": "success",
                "result": result,
                "method": "ddddocr_text",
                "processing_time": round(processing_time, 3)
            }

        except Exception as e:
            self.logger.error(f"文字验证码识别失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "method": "ddddocr_text"
            }

    async def _solve_slide_captcha(self, image_bytes: bytes, captcha_data: Dict[str, Any]) -> Dict[str, Any]:
        """识别滑动验证码"""
        try:
            target_image = captcha_data.get('target_image')
            if not target_image:
                return {
                    "status": "error",
                    "error": "滑动验证码缺少目标图片",
                    "method": "slide"
                }

            # 预处理目标图片
            target_bytes = await self._preprocess_image(target_image)

            # 使用ddddocr的滑动验证码识别
            result = self.slide_ocr.slide_match(target_bytes, image_bytes)

            return {
                "status": "success",
                "result": result,
                "method": "ddddocr_slide"
            }

        except Exception as e:
            self.logger.error(f"滑动验证码识别失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "method": "slide"
            }

    async def _solve_click_captcha(self, image_bytes: bytes, captcha_data: Dict[str, Any]) -> Dict[str, Any]:
        """识别点击验证码"""
        try:
            prompt = captcha_data.get('prompt', '')

            # 使用目标检测识别可点击区域
            positions = self.detect_ocr.detection(image_bytes)

            return {
                "status": "success",
                "result": positions,
                "prompt": prompt,
                "method": "ddddocr_click"
            }

        except Exception as e:
            self.logger.error(f"点击验证码识别失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "method": "click"
            }

    async def _solve_rotate_captcha(self, image_bytes: bytes) -> Dict[str, Any]:
        """识别旋转验证码"""
        try:
            # 旋转验证码通常需要计算旋转角度
            # 这里使用简单的图像处理方法
            image = Image.open(BytesIO(image_bytes))
            image_array = np.array(image)

            # 计算图像的倾斜角度（简化实现）
            # 实际项目中可能需要更复杂的算法
            angle = self._calculate_rotation_angle(image_array)

            return {
                "status": "success",
                "result": angle,
                "method": "rotate_detection"
            }

        except Exception as e:
            self.logger.error(f"旋转验证码识别失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "method": "rotate"
            }

    async def _solve_generic_captcha(self, image_bytes: bytes) -> Dict[str, Any]:
        """通用验证码识别"""
        # 尝试文字识别
        text_result = await self._solve_text_captcha(image_bytes)
        if text_result['status'] == 'success':
            return text_result

        # 尝试目标检测
        try:
            positions = self.detect_ocr.detection(image_bytes)
            return {
                "status": "success",
                "result": positions,
                "method": "generic_detection"
            }
        except:
            pass

        return {
            "status": "error",
            "error": "无法识别验证码类型",
            "method": "generic"
        }

    def _calculate_rotation_angle(self, image_array: np.ndarray) -> float:
        """计算旋转角度（简化实现）"""
        try:
            # 转换为灰度图
            if len(image_array.shape) == 3:
                gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_array

            # 边缘检测
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # 霍夫线变换
            lines = cv2.HoughLines(edges, 1, np.pi/180, 100)

            if lines is not None:
                angles = []
                for line in lines[:10]:  # 只取前10条线
                    rho, theta = line[0]
                    angle = theta * 180 / np.pi
                    if 0 <= angle <= 180:
                        angles.append(angle)

                if angles:
                    # 返回最常见的角度
                    return float(np.median(angles))

            return 0.0

        except Exception as e:
            self.logger.error(f"角度计算失败: {e}")
            return 0.0

    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """计算识别置信度"""
        try:
            if result.get('status') != 'success':
                return 0.0

            method = result.get('method', '')

            if 'ddddocr' in method:
                # ddddocr通常有较高的准确率
                return 0.8
            elif 'detection' in method:
                # 目标检测相对较低
                return 0.6
            else:
                return 0.5

        except:
            return 0.0

    async def batch_solve(self, captcha_list: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """批量识别验证码"""
        results = []
        for captcha_data in captcha_list:
            result = await self.run(captcha_data, **kwargs)
            results.append(result)

            # 添加小延迟避免过快请求
            await asyncio.sleep(0.1)

        return results