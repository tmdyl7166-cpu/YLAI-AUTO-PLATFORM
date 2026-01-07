"""
验证码解决器 - 集成多种OCR引擎
"""

import base64
import logging
import time
from io import BytesIO
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import requests

logger = logging.getLogger(__name__)

class CaptchaSolver:
    """验证码识别和解决器"""

    def __init__(self):
        self.engines = {}
        self._init_engines()

    def _init_engines(self):
        """初始化OCR引擎"""
        try:
            # ddddocr - 本地OCR引擎
            import ddddocr
            self.engines['ddddocr'] = ddddocr.DdddOcr()
            logger.info("ddddocr引擎初始化成功")
        except ImportError:
            logger.warning("ddddocr未安装，跳过")

        try:
            # easyocr - 深度学习OCR
            import easyocr
            self.engines['easyocr'] = easyocr.Reader(['en', 'ch_sim'])
            logger.info("easyocr引擎初始化成功")
        except ImportError:
            logger.warning("easyocr未安装，跳过")

        # 可以添加更多OCR引擎
        # self.engines['tesseract'] = TesseractEngine()

    def solve_captcha(self, image_data: bytes, engine: str = 'auto') -> Tuple[bool, str]:
        """
        解决验证码

        Args:
            image_data: 验证码图片数据
            engine: OCR引擎 ('auto', 'ddddocr', 'easyocr')

        Returns:
            (成功标志, 识别结果)
        """
        if not image_data:
            return False, "图片数据为空"

        # 选择引擎
        if engine == 'auto':
            # 优先使用ddddocr，如果不可用则使用easyocr
            if 'ddddocr' in self.engines:
                engine = 'ddddocr'
            elif 'easyocr' in self.engines:
                engine = 'easyocr'
            else:
                return False, "无可用OCR引擎"

        if engine not in self.engines:
            return False, f"引擎 {engine} 不可用"

        try:
            ocr_engine = self.engines[engine]

            if engine == 'ddddocr':
                result = ocr_engine.classification(image_data)
                confidence = getattr(ocr_engine, 'confidence', 0.5)  # ddddocr可能没有置信度

            elif engine == 'easyocr':
                results = ocr_engine.readtext(image_data)
                if results:
                    # 取置信度最高的识别结果
                    best_result = max(results, key=lambda x: x[2])
                    result = best_result[1]
                    confidence = best_result[2]
                else:
                    return False, "未识别到文字"

            else:
                return False, f"不支持的引擎: {engine}"

            # 清理结果
            result = self._clean_result(result)

            if not result:
                return False, "识别结果为空"

            logger.info(f"验证码识别成功: {result} (引擎: {engine})")
            return True, result

        except Exception as e:
            logger.error(f"验证码识别失败: {e}")
            return False, f"识别错误: {str(e)}"

    def _clean_result(self, text: str) -> str:
        """清理识别结果"""
        if not text:
            return ""

        # 移除空白字符
        text = ''.join(text.split())

        # 只保留字母数字和常见符号
        import re
        text = re.sub(r'[^a-zA-Z0-9]', '', text)

        return text.upper()

    def solve_from_url(self, image_url: str, engine: str = 'auto') -> Tuple[bool, str]:
        """
        从URL解决验证码

        Args:
            image_url: 验证码图片URL

        Returns:
            (成功标志, 识别结果)
        """
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            return self.solve_captcha(response.content, engine)

        except Exception as e:
            logger.error(f"下载验证码图片失败: {e}")
            return False, f"下载失败: {str(e)}"

    def solve_from_base64(self, base64_data: str, engine: str = 'auto') -> Tuple[bool, str]:
        """
        从base64数据解决验证码

        Args:
            base64_data: base64编码的图片数据

        Returns:
            (成功标志, 识别结果)
        """
        try:
            # 移除data URL前缀
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]

            image_data = base64.b64decode(base64_data)
            return self.solve_captcha(image_data, engine)

        except Exception as e:
            logger.error(f"base64解码失败: {e}")
            return False, f"解码失败: {str(e)}"

    def get_available_engines(self) -> list:
        """获取可用引擎列表"""
        return list(self.engines.keys())

    def run_captcha_solver(self, image: Any, **kwargs) -> Dict[str, Any]:
        """
        运行验证码解决器 (API接口)

        Args:
            image: 图片数据 (bytes/URL/base64)
            **kwargs: 额外参数

        Returns:
            解决结果
        """
        engine = kwargs.get('engine', 'auto')
        timeout = kwargs.get('timeout', 30)

        start_time = time.time()

        try:
            if isinstance(image, str):
                if image.startswith('http'):
                    success, result = self.solve_from_url(image, engine)
                elif image.startswith('data:'):
                    success, result = self.solve_from_base64(image, engine)
                else:
                    # 假设是base64
                    success, result = self.solve_from_base64(image, engine)
            elif isinstance(image, bytes):
                success, result = self.solve_captcha(image, engine)
            else:
                return {
                    "success": False,
                    "result": "",
                    "error": "不支持的图片格式",
                    "engine": engine,
                    "time_taken": time.time() - start_time
                }

            return {
                "success": success,
                "result": result,
                "engine": engine,
                "time_taken": time.time() - start_time,
                "available_engines": self.get_available_engines()
            }

        except Exception as e:
            logger.error(f"验证码解决器运行失败: {e}")
            return {
                "success": False,
                "result": "",
                "error": str(e),
                "engine": engine,
                "time_taken": time.time() - start_time
            }