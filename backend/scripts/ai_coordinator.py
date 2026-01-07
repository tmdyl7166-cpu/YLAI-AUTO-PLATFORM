#!/usr/bin/env python3
"""
AI模型联动协调器
实现四个本地AI模型的专用性功能联动
"""

import asyncio
import json
import time
import aiohttp
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import os

from backend.core.base import BaseScript


class ModelRole(Enum):
    """模型角色枚举"""
    CONTENT_UNDERSTANDING = "content_understanding"  # 内容理解
    TASK_PLANNING = "task_planning"              # 任务规划
    COMPLEX_REASONING = "complex_reasoning"      # 复杂推理
    CREATIVE_GENERATION = "creative_generation"  # 创意生成


@dataclass
class AIModel:
    """AI模型配置"""
    name: str
    role: ModelRole
    url: str
    port: int
    priority: int  # 优先级 (1-4, 1最高)
    capabilities: List[str]
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 60

    @property
    def endpoint(self) -> str:
        return f"{self.url}/api/generate"


@dataclass
class TaskContext:
    """任务上下文"""
    task_id: str
    task_type: str
    input_data: Any
    current_stage: str
    model_history: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    created_at: float
    completed_at: Optional[float] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.model_history is None:
            self.model_history = []
        if self.metadata is None:
            self.metadata = {}


class AIModelCoordinator(BaseScript):
    """AI模型联动协调器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 模型配置
        self.models: Dict[str, AIModel] = {}

        # 任务上下文
        self.active_tasks: Dict[str, TaskContext] = {}

        # 联动配置
        self.linkage_config = {
            'content_analysis': ['qwen3', 'llama3.1'],      # 内容分析：qwen3 -> llama3.1
            'task_planning': ['llama3.1', 'deepseek-r1'],   # 任务规划：llama3.1 -> deepseek-r1
            'decision_making': ['deepseek-r1'],             # 决策制定：deepseek-r1
            'content_generation': ['gpt-oss', 'qwen3'],     # 内容生成：gpt-oss -> qwen3
            'code_generation': ['deepseek-r1', 'llama3.1'], # 代码生成：deepseek-r1 -> llama3.1
            'complex_reasoning': ['deepseek-r1', 'gpt-oss'], # 复杂推理：deepseek-r1 -> gpt-oss
        }

        # 性能监控
        self.performance_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'model_usage': {},
            'task_completion_rate': 0.0
        }

        # HTTP客户端
        self.session: Optional[aiohttp.ClientSession] = None

        # 初始化模型
        self._init_models()

    def _init_models(self):
        """初始化模型配置"""
        # 从环境变量读取配置
        models_config = {
            'qwen3': {
                'name': 'qwen3:8b',
                'role': ModelRole.CONTENT_UNDERSTANDING,
                'url': os.getenv('QWEN_URL', 'http://localhost:11434'),
                'port': int(os.getenv('QWEN_PORT', '11434')),
                'priority': 1,
                'capabilities': ['chinese_processing', 'content_analysis', 'document_understanding'],
                'max_tokens': 8192,
                'temperature': 0.3
            },
            'llama3.1': {
                'name': 'llama3.1:8b',
                'role': ModelRole.TASK_PLANNING,
                'url': os.getenv('LLAMA_URL', 'http://localhost:11435'),
                'port': int(os.getenv('LLAMA_PORT', '11435')),
                'priority': 2,
                'capabilities': ['task_planning', 'instruction_understanding', 'coordination'],
                'max_tokens': 4096,
                'temperature': 0.5
            },
            'deepseek-r1': {
                'name': 'deepseek-r1:8b',
                'role': ModelRole.COMPLEX_REASONING,
                'url': os.getenv('DEEPSEEK_URL', 'http://localhost:11436'),
                'port': int(os.getenv('DEEPSEEK_PORT', '11436')),
                'priority': 3,
                'capabilities': ['complex_reasoning', 'mathematical_calculation', 'code_generation', 'decision_making'],
                'max_tokens': 16384,
                'temperature': 0.1
            },
            'gpt-oss': {
                'name': 'gpt-oss:20b',
                'role': ModelRole.CREATIVE_GENERATION,
                'url': os.getenv('GPTOSS_URL', 'http://localhost:11437'),
                'port': int(os.getenv('GPTOSS_PORT', '11437')),
                'priority': 4,
                'capabilities': ['creative_writing', 'text_generation', 'content_enhancement', 'diverse_output'],
                'max_tokens': 8192,
                'temperature': 0.8
            }
        }

        for model_id, config in models_config.items():
            self.models[model_id] = AIModel(**config)

    async def initialize(self):
        """初始化协调器"""
        await super().initialize()

        # 初始化HTTP客户端
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=300)  # 5分钟超时
            )

        # 检查模型连接
        await self._check_model_connectivity()

    async def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """执行AI协调操作"""
        try:
            self.logger.info(f"执行AI协调操作: {action}")

            # 预运行检查
            await self.pre_run()

            # 执行操作
            if action == 'process_task':
                result = await self._process_task(**kwargs)
            elif action == 'analyze_content':
                result = await self._analyze_content(**kwargs)
            elif action == 'generate_plan':
                result = await self._generate_plan(**kwargs)
            elif action == 'make_decision':
                result = await self._make_decision(**kwargs)
            elif action == 'create_content':
                result = await self._create_content(**kwargs)
            elif action == 'get_model_status':
                result = await self._get_model_status()
            elif action == 'get_performance_stats':
                result = await self._get_performance_stats()
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

    async def _process_task(self, task_type: str, input_data: Any,
                          task_id: str = None, **kwargs) -> Dict[str, Any]:
        """处理任务（联动流程）"""
        try:
            if task_id is None:
                task_id = f"task_{int(time.time())}_{hash(str(input_data)) % 10000}"

            # 创建任务上下文
            context = TaskContext(
                task_id=task_id,
                task_type=task_type,
                input_data=input_data,
                current_stage='initiated',
                metadata=kwargs
            )

            self.active_tasks[task_id] = context

            # 根据任务类型确定联动流程
            workflow = self._get_workflow_for_task(task_type)
            if not workflow:
                return {"status": "error", "error": f"不支持的任务类型: {task_type}"}

            # 执行联动流程
            result = await self._execute_workflow(context, workflow)

            # 更新任务状态
            context.completed_at = time.time()
            context.current_stage = 'completed'

            return {
                "status": "success",
                "task_id": task_id,
                "result": result,
                "workflow": workflow,
                "processing_time": context.completed_at - context.created_at
            }

        except Exception as e:
            self.logger.error(f"任务处理失败: {e}")
            if task_id and task_id in self.active_tasks:
                self.active_tasks[task_id].current_stage = 'failed'
            return {"status": "error", "error": f"任务处理失败: {e}"}

    def _get_workflow_for_task(self, task_type: str) -> List[str]:
        """获取任务的工作流"""
        return self.linkage_config.get(task_type, [])

    async def _execute_workflow(self, context: TaskContext, workflow: List[str]) -> Dict[str, Any]:
        """执行工作流"""
        current_input = context.input_data
        workflow_results = {}

        for stage, model_id in enumerate(workflow):
            if model_id not in self.models:
                raise ValueError(f"模型 {model_id} 不存在")

            model = self.models[model_id]
            context.current_stage = f"processing_{model_id}"

            # 准备提示词
            prompt = self._prepare_prompt_for_stage(
                context.task_type, stage, model_id, current_input, context.metadata
            )

            # 调用模型
            start_time = time.time()
            response = await self._call_model(model, prompt)
            processing_time = time.time() - start_time

            # 记录到历史
            context.model_history.append({
                'stage': stage,
                'model': model_id,
                'input': current_input,
                'output': response.get('text', ''),
                'processing_time': processing_time,
                'success': response.get('status') == 'success'
            })

            if response.get('status') != 'success':
                raise RuntimeError(f"模型 {model_id} 调用失败: {response.get('error', 'unknown')}")

            # 更新输入为当前输出
            current_input = response['text']
            workflow_results[model_id] = response

            # 更新性能统计
            self._update_performance_stats(model_id, processing_time, True)

        return {
            'final_output': current_input,
            'workflow_results': workflow_results,
            'model_history': context.model_history
        }

    def _prepare_prompt_for_stage(self, task_type: str, stage: int,
                                model_id: str, input_data: Any, metadata: Dict[str, Any]) -> str:
        """为阶段准备提示词"""
        base_prompts = {
            'content_analysis': {
                'qwen3': "请分析以下内容的主题、情感和关键信息，用中文回答：\n\n{content}",
                'llama3.1': "基于内容分析结果，制定处理计划：\n\n{previous_output}"
            },
            'task_planning': {
                'llama3.1': "请理解用户指令并制定执行计划：\n\n{instruction}",
                'deepseek-r1': "基于任务计划，进行推理和优化：\n\n{previous_output}"
            },
            'decision_making': {
                'deepseek-r1': "请分析选项并做出最佳决策：\n\n{options}"
            },
            'content_generation': {
                'gpt-oss': "请根据要求生成创意内容：\n\n{requirements}",
                'qwen3': "优化和润色以下内容：\n\n{previous_output}"
            },
            'code_generation': {
                'deepseek-r1': "生成高质量的代码：\n\n{specification}",
                'llama3.1': "检查和改进代码质量：\n\n{previous_output}"
            },
            'complex_reasoning': {
                'deepseek-r1': "进行深度推理分析：\n\n{problem}",
                'gpt-oss': "基于推理结果生成解决方案：\n\n{previous_output}"
            }
        }

        task_prompts = base_prompts.get(task_type, {})
        prompt_template = task_prompts.get(model_id, "请处理以下内容：\n\n{content}")

        # 替换变量
        if isinstance(input_data, str):
            content = input_data
        else:
            content = json.dumps(input_data, ensure_ascii=False, indent=2)

        prompt = prompt_template.replace("{content}", content)
        prompt = prompt.replace("{previous_output}", content)
        prompt = prompt.replace("{instruction}", content)
        prompt = prompt.replace("{options}", content)
        prompt = prompt.replace("{requirements}", content)
        prompt = prompt.replace("{specification}", content)
        prompt = prompt.replace("{problem}", content)

        return prompt

    async def _call_model(self, model: AIModel, prompt: str) -> Dict[str, Any]:
        """调用模型"""
        try:
            payload = {
                "model": model.name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": model.temperature,
                    "num_predict": min(model.max_tokens, 4096),
                    "top_p": 0.9,
                    "top_k": 40
                }
            }

            async with self.session.post(model.endpoint, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    text = data.get('response', '').strip()

                    return {
                        "status": "success",
                        "text": text,
                        "model": model.name,
                        "tokens_used": len(text.split()),
                        "processing_time": data.get('total_duration', 0) / 1e9  # 转换为秒
                    }
                else:
                    error_text = await resp.text()
                    return {
                        "status": "error",
                        "error": f"HTTP {resp.status}: {error_text}"
                    }

        except Exception as e:
            self.logger.error(f"模型调用失败 {model.name}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _analyze_content(self, content: str, **kwargs) -> Dict[str, Any]:
        """内容分析（qwen3 -> llama3.1）"""
        return await self._process_task('content_analysis', content, **kwargs)

    async def _generate_plan(self, instruction: str, **kwargs) -> Dict[str, Any]:
        """生成计划（llama3.1 -> deepseek-r1）"""
        return await self._process_task('task_planning', instruction, **kwargs)

    async def _make_decision(self, options: str, **kwargs) -> Dict[str, Any]:
        """决策制定（deepseek-r1）"""
        return await self._process_task('decision_making', options, **kwargs)

    async def _create_content(self, requirements: str, **kwargs) -> Dict[str, Any]:
        """内容创作（gpt-oss -> qwen3）"""
        return await self._process_task('content_generation', requirements, **kwargs)

    async def _get_model_status(self) -> Dict[str, Any]:
        """获取模型状态"""
        status_info = {}
        for model_id, model in self.models.items():
            # 检查模型是否可访问
            try:
                async with self.session.get(f"{model.url}/api/tags", timeout=5) as resp:
                    is_available = resp.status == 200
            except:
                is_available = False

            status_info[model_id] = {
                'name': model.name,
                'role': model.role.value,
                'available': is_available,
                'url': model.url,
                'capabilities': model.capabilities
            }

        return {
            "status": "success",
            "models": status_info,
            "total_models": len(self.models),
            "available_models": sum(1 for s in status_info.values() if s['available'])
        }

    async def _get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            "status": "success",
            "stats": self.performance_stats,
            "active_tasks": len(self.active_tasks),
            "models": {k: asdict(v) for k, v in self.models.items()}
        }

    async def _check_model_connectivity(self):
        """检查模型连接性"""
        self.logger.info("检查模型连接性...")

        for model_id, model in self.models.items():
            try:
                async with self.session.get(f"{model.url}/api/tags", timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models_list = [m['name'] for m in data.get('models', [])]
                        if model.name in models_list:
                            self.logger.info(f"模型 {model_id} ({model.name}) 连接正常")
                        else:
                            self.logger.warning(f"模型 {model_id} ({model.name}) 未找到，可用模型: {models_list}")
                    else:
                        self.logger.warning(f"模型 {model_id} 服务响应异常: {resp.status}")
            except Exception as e:
                self.logger.error(f"模型 {model_id} 连接失败: {e}")

    def _update_performance_stats(self, model_id: str, processing_time: float, success: bool):
        """更新性能统计"""
        self.performance_stats['total_requests'] += 1

        if success:
            self.performance_stats['successful_requests'] += 1
        else:
            self.performance_stats['failed_requests'] += 1

        # 更新平均响应时间
        total_time = self.performance_stats['avg_response_time'] * (self.performance_stats['total_requests'] - 1)
        self.performance_stats['avg_response_time'] = (total_time + processing_time) / self.performance_stats['total_requests']

        # 更新模型使用统计
        if model_id not in self.performance_stats['model_usage']:
            self.performance_stats['model_usage'][model_id] = 0
        self.performance_stats['model_usage'][model_id] += 1

    async def cleanup(self):
        """清理资源"""
        if self.session:
            await self.session.close()

        # 清理完成的任务
        current_time = time.time()
        completed_tasks = [
            task_id for task_id, context in self.active_tasks.items()
            if context.completed_at and (current_time - context.completed_at) > 3600  # 1小时后清理
        ]

        for task_id in completed_tasks:
            del self.active_tasks[task_id]

        await super().cleanup()