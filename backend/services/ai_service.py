#!/usr/bin/env python3
"""
AI服务集成模块
提供AI模型推理、训练和优化服务
"""

import asyncio
import json
import time
import aiohttp
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime

from backend.core.base import BaseScript


@dataclass
class AIModel:
    """AI模型信息"""
    name: str
    version: str
    type: str  # 'text', 'image', 'multimodal'
    capabilities: List[str]
    status: str  # 'available', 'training', 'error'
    performance: Dict[str, float]
    last_used: float
    created_at: float

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.last_used is None:
            self.last_used = time.time()


@dataclass
class InferenceRequest:
    """推理请求"""
    model: str
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.stop_sequences is None:
            self.stop_sequences = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class InferenceResponse:
    """推理响应"""
    model: str
    text: str
    tokens_used: int
    finish_reason: str
    processing_time: float
    metadata: Dict[str, Any]


class AIService(BaseScript):
    """AI服务"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # AI服务配置
        self.config = {
            'ollama_url': 'http://localhost:11434',
            'ai_docker_url': 'http://localhost:9001',
            'default_model': 'qwen2.5:3b',
            'timeout': 60.0,
            'max_retries': 3,
            'batch_size': 10,
            'cache_enabled': True,
            'cache_ttl': 3600,  # 1小时
            'model_switch_timeout': 300.0,  # 5分钟
        }

        # 模型管理
        self.models: Dict[str, AIModel] = {}
        self.current_model: Optional[str] = None

        # 缓存
        self.cache: Dict[str, Dict[str, Any]] = {}

        # 统计信息
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens': 0,
            'avg_response_time': 0.0,
            'model_usage': {},
            'cache_hits': 0,
            'cache_misses': 0
        }

        # HTTP客户端
        self.session: Optional[aiohttp.ClientSession] = None

    async def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """执行AI服务操作"""
        try:
            self.logger.info(f"执行AI服务操作: {action}")

            # 预运行检查
            await self.pre_run()

            # 执行操作
            if action == 'generate':
                result = await self._generate_text(**kwargs)
            elif action == 'analyze_image':
                result = await self._analyze_image(**kwargs)
            elif action == 'train_model':
                result = await self._train_model(**kwargs)
            elif action == 'list_models':
                result = await self._list_models()
            elif action == 'switch_model':
                result = await self._switch_model(**kwargs)
            elif action == 'optimize_code':
                result = await self._optimize_code(**kwargs)
            elif action == 'get_stats':
                result = await self._get_stats()
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

    async def pre_run(self):
        """预运行初始化"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config['timeout'])
            )

        # 确保AI服务可用
        await self._ensure_ai_service()

    async def post_run(self, result: Dict[str, Any]):
        """后运行清理"""
        # 更新统计信息
        if result.get("status") == "success":
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1

        self.stats['total_requests'] += 1

    async def on_error(self, error: Exception):
        """错误处理"""
        self.logger.error(f"AI服务错误: {error}")
        self.stats['failed_requests'] += 1

    async def _ensure_ai_service(self):
        """确保AI服务可用"""
        try:
            # 检查Ollama服务
            async with self.session.get(f"{self.config['ollama_url']}/api/tags") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self._update_models_from_ollama(data)
                    self.logger.info("Ollama服务连接成功")
                else:
                    self.logger.warning(f"Ollama服务状态异常: {resp.status}")

            # 检查AI Docker服务
            async with self.session.get(f"{self.config['ai_docker_url']}/health") as resp:
                if resp.status == 200:
                    self.logger.info("AI Docker服务连接成功")
                else:
                    self.logger.warning(f"AI Docker服务状态异常: {resp.status}")

        except Exception as e:
            self.logger.warning(f"AI服务连接检查失败: {e}")

    def _update_models_from_ollama(self, data: Dict[str, Any]):
        """从Ollama更新模型信息"""
        if 'models' in data:
            for model_info in data['models']:
                name = model_info.get('name', '')
                if name:
                    self.models[name] = AIModel(
                        name=name,
                        version=model_info.get('modified_at', ''),
                        type='text',  # 假设都是文本模型
                        capabilities=['generate', 'chat'],
                        status='available',
                        performance={'size': model_info.get('size', 0)},
                        last_used=time.time(),
                        created_at=time.time()
                    )

    async def _generate_text(self, prompt: str, model: str = None,
                           temperature: float = 0.7, max_tokens: int = 512,
                           **kwargs) -> Dict[str, Any]:
        """生成文本"""
        start_time = time.time()

        try:
            # 缓存检查
            cache_key = self._get_cache_key(prompt, model, temperature, max_tokens)
            if self.config['cache_enabled'] and cache_key in self.cache:
                cached_result = self.cache[cache_key]
                if time.time() - cached_result['timestamp'] < self.config['cache_ttl']:
                    self.stats['cache_hits'] += 1
                    return {
                        "status": "success",
                        "text": cached_result['text'],
                        "cached": True,
                        "processing_time": time.time() - start_time
                    }

            self.stats['cache_misses'] += 1

            # 选择模型
            model_name = model or self.current_model or self.config['default_model']

            # 准备请求
            request_data = {
                "model": model_name,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }

            # 发送请求到Ollama
            async with self.session.post(
                f"{self.config['ollama_url']}/api/generate",
                json=request_data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    text = data.get('response', '')
                    tokens_used = len(text.split())  # 粗略估算

                    processing_time = time.time() - start_time

                    # 更新统计
                    self.stats['total_tokens'] += tokens_used
                    self.stats['avg_response_time'] = (
                        (self.stats['avg_response_time'] * (self.stats['total_requests'] - 1)) +
                        processing_time
                    ) / self.stats['total_requests']

                    # 更新模型使用统计
                    if model_name not in self.stats['model_usage']:
                        self.stats['model_usage'][model_name] = 0
                    self.stats['model_usage'][model_name] += 1

                    # 缓存结果
                    if self.config['cache_enabled']:
                        self.cache[cache_key] = {
                            'text': text,
                            'timestamp': time.time()
                        }

                    return {
                        "status": "success",
                        "text": text,
                        "model": model_name,
                        "tokens_used": tokens_used,
                        "processing_time": round(processing_time, 3),
                        "cached": False
                    }
                else:
                    error_text = await resp.text()
                    return {
                        "status": "error",
                        "error": f"AI服务错误: {resp.status} - {error_text}",
                        "processing_time": round(time.time() - start_time, 3)
                    }

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"文本生成失败: {e}")
            return {
                "status": "error",
                "error": f"文本生成失败: {e}",
                "processing_time": round(processing_time, 3)
            }

    async def _analyze_image(self, image_path: str, prompt: str = None,
                           model: str = None, **kwargs) -> Dict[str, Any]:
        """分析图像"""
        try:
            # 这里可以集成图像识别模型
            # 目前返回占位符实现
            return {
                "status": "success",
                "analysis": "图像分析功能待实现",
                "image_path": image_path,
                "prompt": prompt or "分析这张图片"
            }

        except Exception as e:
            self.logger.error(f"图像分析失败: {e}")
            return {"status": "error", "error": f"图像分析失败: {e}"}

    async def _train_model(self, dataset_path: str, model_type: str = 'text',
                         epochs: int = 10, **kwargs) -> Dict[str, Any]:
        """训练模型"""
        try:
            # 这里可以实现模型训练逻辑
            # 目前返回占位符实现
            return {
                "status": "success",
                "message": "模型训练功能待实现",
                "dataset_path": dataset_path,
                "model_type": model_type,
                "epochs": epochs
            }

        except Exception as e:
            self.logger.error(f"模型训练失败: {e}")
            return {"status": "error", "error": f"模型训练失败: {e}"}

    async def _list_models(self) -> Dict[str, Any]:
        """列出可用模型"""
        try:
            models_info = []
            for name, model in self.models.items():
                models_info.append(asdict(model))

            return {
                "status": "success",
                "models": models_info,
                "current_model": self.current_model,
                "total_models": len(models_info)
            }

        except Exception as e:
            self.logger.error(f"列出模型失败: {e}")
            return {"status": "error", "error": f"列出模型失败: {e}"}

    async def _switch_model(self, model_name: str, **kwargs) -> Dict[str, Any]:
        """切换模型"""
        try:
            if model_name not in self.models:
                return {"status": "error", "error": f"模型不存在: {model_name}"}

            # 检查模型状态
            model = self.models[model_name]
            if model.status != 'available':
                return {"status": "error", "error": f"模型不可用: {model.status}"}

            # 切换模型
            self.current_model = model_name
            model.last_used = time.time()

            return {
                "status": "success",
                "model": model_name,
                "capabilities": model.capabilities,
                "performance": model.performance
            }

        except Exception as e:
            self.logger.error(f"切换模型失败: {e}")
            return {"status": "error", "error": f"切换模型失败: {e}"}

    async def _optimize_code(self, code: str, language: str = 'python',
                           **kwargs) -> Dict[str, Any]:
        """优化代码"""
        try:
            prompt = f"""请优化以下{language}代码，提高性能、可读性和最佳实践：

```python
{code}
```

请提供优化后的代码和改进说明。"""

            result = await self._generate_text(
                prompt=prompt,
                model=self.current_model,
                temperature=0.2,  # 降低创造性，提高准确性
                max_tokens=1024
            )

            if result['status'] == 'success':
                return {
                    "status": "success",
                    "original_code": code,
                    "optimized_code": result['text'],
                    "language": language,
                    "processing_time": result['processing_time']
                }
            else:
                return result

        except Exception as e:
            self.logger.error(f"代码优化失败: {e}")
            return {"status": "error", "error": f"代码优化失败: {e}"}

    async def _get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            return {
                "status": "success",
                "stats": self.stats,
                "current_model": self.current_model,
                "cache_size": len(self.cache),
                "models_count": len(self.models)
            }

        except Exception as e:
            self.logger.error(f"获取统计失败: {e}")
            return {"status": "error", "error": f"获取统计失败: {e}"}

    def _get_cache_key(self, prompt: str, model: str, temperature: float, max_tokens: int) -> str:
        """生成缓存键"""
        import hashlib
        key_data = f"{prompt}|{model}|{temperature}|{max_tokens}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def batch_generate(self, requests: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """批量生成"""
        results = []
        successful = 0
        failed = 0

        for req in requests:
            result = await self._generate_text(**req, **kwargs)
            results.append(result)

            if result['status'] == 'success':
                successful += 1
            else:
                failed += 1

        return {
            "status": "success",
            "total_requests": len(requests),
            "successful": successful,
            "failed": failed,
            "results": results
        }

    async def close(self):
        """关闭服务"""
        if self.session:
            await self.session.close()
            self.session = None