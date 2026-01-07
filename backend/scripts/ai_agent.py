#!/usr/bin/env python3
"""
AI增强智能代理
集成AI模型进行智能任务执行、逆向推理和自动化决策
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import re

from backend.core.base import BaseScript
from backend.core.registry import registry
from backend.scripts.ai_coordinator import AIModelCoordinator


@dataclass
class AgentTask:
    """代理任务"""
    task_id: str
    task_type: str
    description: str
    parameters: Dict[str, Any]
    priority: int  # 1-5, 5最高
    dependencies: List[str]  # 依赖的任务ID
    status: str  # 'pending', 'running', 'completed', 'failed'
    created_at: Optional[float] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    reverse_engineering: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.parameters is None:
            self.parameters = {}
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class AgentWorkflow:
    """代理工作流"""
    workflow_id: str
    name: str
    description: str
    tasks: List[AgentTask]
    status: str  # 'planning', 'executing', 'completed', 'failed'
    ai_generated: bool = False
    created_at: Optional[float] = None
    completed_at: Optional[float] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.tasks is None:
            self.tasks = []


@registry.register("ai_agent")
class AIAgentScript(BaseScript):
    """AI增强智能代理"""

    name = "ai_agent"
    description = "AI增强智能代理"
    version = "2.0.0"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # AI协调器
        self.ai_coordinator = None

        # 任务队列
        self.task_queue: List[AgentTask] = []
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: Dict[str, AgentTask] = {}

        # 工作流
        self.workflows: Dict[str, AgentWorkflow] = {}

        # 代理配置
        self.config = {
            'max_concurrent_tasks': 3,
            'task_timeout': 300,  # 5分钟
            'auto_optimization': True,
            'learning_enabled': True,
            'reverse_engineering': True,
            'decision_threshold': 0.8,
        }

        # 性能统计
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'avg_execution_time': 0.0,
            'ai_decisions': 0,
            'reverse_engineering_sessions': 0,
        }

    async def pre_run(self, **kwargs):
        """初始化AI协调器"""
        await super().pre_run(**kwargs)

        # 初始化AI协调器
        try:
            self.ai_coordinator = AIModelCoordinator()
            await self.ai_coordinator.initialize()
            self.logger.info("✅ AI协调器初始化成功")
        except Exception as e:
            self.logger.warning(f"⚠️ AI协调器初始化失败: {e}")
            self.ai_coordinator = None

    async def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        执行AI代理操作
        参数:
            action: 操作类型 ('create_task', 'execute_workflow', 'analyze_system', 'reverse_engineer')
        """
        try:
            self.logger.info(f"🤖 AI代理执行操作: {action}")

            if action == 'create_task':
                result = await self._create_ai_task(**kwargs)
            elif action == 'execute_workflow':
                result = await self._execute_workflow(**kwargs)
            elif action == 'analyze_system':
                result = await self._analyze_system(**kwargs)
            elif action == 'reverse_engineer':
                result = await self._reverse_engineer_target(**kwargs)
            elif action == 'optimize_strategy':
                result = await self._optimize_strategy(**kwargs)
            else:
                result = {"status": "error", "error": f"未知操作: {action}"}

            return result

        except Exception as e:
            self.logger.error(f"AI代理执行失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _create_ai_task(self, task_type: str, description: str, **kwargs) -> Dict[str, Any]:
        """AI辅助创建任务"""
        try:
            # 使用AI分析任务需求
            if self.ai_coordinator:
                analysis_prompt = f"""
                分析任务需求并优化任务定义：
                任务类型: {task_type}
                描述: {description}
                参数: {kwargs}

                请提供：
                1. 任务优先级评估
                2. 所需资源和依赖
                3. 执行策略建议
                4. 潜在风险评估
                """

                analysis = await self.ai_coordinator.run('task_planning', content=analysis_prompt)

                if analysis.get('status') == 'success':
                    ai_suggestions = analysis.get('result', {})
                    priority = ai_suggestions.get('priority', 3)
                    dependencies = ai_suggestions.get('dependencies', [])
                    optimized_params = ai_suggestions.get('optimized_params', kwargs)
                else:
                    priority = kwargs.get('priority', 3)
                    dependencies = kwargs.get('dependencies', [])
                    optimized_params = kwargs
            else:
                priority = kwargs.get('priority', 3)
                dependencies = kwargs.get('dependencies', [])
                optimized_params = kwargs

            # 创建任务
            task_id = f"task_{int(time.time())}_{hash(description) % 10000}"
            task = AgentTask(
                task_id=task_id,
                task_type=task_type,
                description=description,
                parameters=optimized_params,
                priority=priority,
                dependencies=dependencies,
                status='pending'
            )

            self.task_queue.append(task)
            self.stats['total_tasks'] += 1

            self.logger.info(f"✅ AI任务创建成功: {task_id}")

            return {
                "status": "success",
                "task_id": task_id,
                "task": asdict(task),
                "ai_optimized": bool(self.ai_coordinator)
            }

        except Exception as e:
            self.logger.error(f"创建AI任务失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _execute_workflow(self, workflow_name: str, **kwargs) -> Dict[str, Any]:
        """执行AI生成的工作流"""
        try:
            # AI生成工作流
            if self.ai_coordinator:
                workflow_prompt = f"""
                为以下需求生成完整的工作流：
                工作流名称: {workflow_name}
                需求描述: {kwargs.get('description', '未指定')}
                目标: {kwargs.get('target', '未指定')}

                请生成：
                1. 工作流步骤分解
                2. 各步骤依赖关系
                3. 执行顺序和优先级
                4. 错误处理策略
                5. 性能优化建议
                """

                workflow_plan = await self.ai_coordinator.run('task_planning', content=workflow_prompt)

                if workflow_plan.get('status') == 'success':
                    plan = workflow_plan.get('result', {})
                    tasks = []

                    # 将AI生成的计划转换为任务
                    for step in plan.get('steps', []):
                        task = AgentTask(
                            task_id=f"wf_{workflow_name}_{step['id']}",
                            task_type=step.get('type', 'generic'),
                            description=step.get('description', ''),
                            parameters=step.get('parameters', {}),
                            priority=step.get('priority', 3),
                            dependencies=step.get('dependencies', []),
                            status='pending'
                        )
                        tasks.append(task)

                    # 创建工作流
                    workflow = AgentWorkflow(
                        workflow_id=f"wf_{int(time.time())}",
                        name=workflow_name,
                        description=kwargs.get('description', ''),
                        tasks=tasks,
                        status='planning',
                        ai_generated=True
                    )

                    self.workflows[workflow.workflow_id] = workflow

                    # 执行工作流
                    result = await self._execute_workflow_tasks(workflow)
                    return result
                else:
                    return {"status": "error", "error": "AI工作流生成失败"}
            else:
                return {"status": "error", "error": "AI协调器未启用，无法生成工作流"}

        except Exception as e:
            self.logger.error(f"执行工作流失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _execute_workflow_tasks(self, workflow: AgentWorkflow) -> Dict[str, Any]:
        """执行工作流任务"""
        try:
            workflow.status = 'executing'
            completed_tasks = []
            failed_tasks = []

            # 按依赖关系排序任务
            sorted_tasks = self._topological_sort(workflow.tasks)

            for task in sorted_tasks:
                # 检查依赖
                if not self._check_dependencies(task, completed_tasks):
                    failed_tasks.append(task.task_id)
                    continue

                # 执行任务
                task.started_at = time.time()
                task.status = 'running'

                try:
                    result = await self._execute_single_task(task)
                    task.result = result
                    task.completed_at = time.time()
                    task.status = 'completed'
                    completed_tasks.append(task.task_id)

                    self.logger.info(f"✅ 任务完成: {task.task_id}")

                except Exception as e:
                    task.status = 'failed'
                    task.result = {"error": str(e)}
                    failed_tasks.append(task.task_id)
                    self.logger.error(f"❌ 任务失败: {task.task_id} - {e}")

            # 更新工作流状态
            if failed_tasks:
                workflow.status = 'failed'
            else:
                workflow.status = 'completed'
                workflow.completed_at = time.time()

            return {
                "status": "success",
                "workflow_id": workflow.workflow_id,
                "completed_tasks": len(completed_tasks),
                "failed_tasks": len(failed_tasks),
                "execution_time": workflow.completed_at - workflow.created_at if workflow.completed_at else 0
            }

        except Exception as e:
            workflow.status = 'failed'
            self.logger.error(f"工作流执行失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _execute_single_task(self, task: AgentTask) -> Dict[str, Any]:
        """执行单个任务"""
        try:
            # 根据任务类型调用相应的处理逻辑
            if task.task_type == 'data_collection':
                result = await self._execute_data_collection_task(task)
            elif task.task_type == 'analysis':
                result = await self._execute_analysis_task(task)
            elif task.task_type == 'reverse_engineering':
                result = await self._execute_reverse_engineering_task(task)
            elif task.task_type == 'optimization':
                result = await self._execute_optimization_task(task)
            else:
                # 通用任务执行
                result = await self._execute_generic_task(task)

            return result

        except Exception as e:
            self.logger.error(f"任务执行失败: {task.task_id} - {e}")
            raise

    async def _execute_data_collection_task(self, task: AgentTask) -> Dict[str, Any]:
        """执行数据收集任务"""
        # 调用数据收集器
        from backend.scripts.data_collector import DataCollector

        collector = DataCollector()
        await collector.initialize()

        result = await collector.run('collect_data', **task.parameters)
        return result

    async def _execute_analysis_task(self, task: AgentTask) -> Dict[str, Any]:
        """执行分析任务"""
        if not self.ai_coordinator:
            return {"status": "error", "error": "AI协调器未启用"}

        analysis_result = await self.ai_coordinator.run(
            'complex_reasoning',
            content=task.parameters.get('content', '')
        )

        return analysis_result

    async def _execute_reverse_engineering_task(self, task: AgentTask) -> Dict[str, Any]:
        """执行逆向工程任务"""
        if not self.ai_coordinator:
            return {"status": "error", "error": "AI协调器未启用"}

        target = task.parameters.get('target', '')
        analysis_type = task.parameters.get('analysis_type', 'architecture')

        prompt = f"""
        对以下目标进行逆向工程分析：
        目标: {target}
        分析类型: {analysis_type}

        请分析：
        1. 系统架构和组件
        2. 数据流和处理逻辑
        3. API接口和通信协议
        4. 安全机制和漏洞
        5. 性能特征和瓶颈
        6. 扩展和优化建议
        """

        result = await self.ai_coordinator.run('complex_reasoning', content=prompt)
        self.stats['reverse_engineering_sessions'] += 1

        return result

    async def _execute_optimization_task(self, task: AgentTask) -> Dict[str, Any]:
        """执行优化任务"""
        if not self.ai_coordinator:
            return {"status": "error", "error": "AI协调器未启用"}

        target_system = task.parameters.get('target_system', '')
        optimization_goal = task.parameters.get('goal', 'performance')

        prompt = f"""
        优化以下系统：
        目标系统: {target_system}
        优化目标: {optimization_goal}

        请提供：
        1. 当前系统分析
        2. 性能瓶颈识别
        3. 优化策略建议
        4. 实施计划
        5. 预期效果评估
        """

        result = await self.ai_coordinator.run('task_planning', content=prompt)
        return result

    async def _execute_generic_task(self, task: AgentTask) -> Dict[str, Any]:
        """执行通用任务"""
        # 使用AI生成执行计划
        if self.ai_coordinator:
            prompt = f"执行任务: {task.description}\n参数: {task.parameters}"

            result = await self.ai_coordinator.run('task_planning', content=prompt)
            return result
        else:
            return {"status": "completed", "message": f"任务 {task.task_id} 已执行"}

    async def _analyze_system(self, target_system: str, **kwargs) -> Dict[str, Any]:
        """系统分析"""
        try:
            analysis_prompt = f"""
            分析目标系统：
            系统: {target_system}
            分析范围: {kwargs.get('scope', '全面分析')}

            请提供：
            1. 系统架构分析
            2. 功能模块识别
            3. 数据流分析
            4. 性能评估
            5. 安全评估
            6. 改进建议
            """

            if self.ai_coordinator:
                result = await self.ai_coordinator.run('complex_reasoning', content=analysis_prompt)
                return result
            else:
                return {"status": "error", "error": "AI协调器未启用"}

        except Exception as e:
            self.logger.error(f"系统分析失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _reverse_engineer_target(self, target: str, **kwargs) -> Dict[str, Any]:
        """逆向工程目标系统"""
        try:
            reverse_prompt = f"""
            逆向工程分析目标：
            目标: {target}
            分析深度: {kwargs.get('depth', '深度分析')}

            请分析：
            1. 技术栈识别
            2. 架构模式推断
            3. API接口分析
            4. 数据结构分析
            5. 安全机制分析
            6. 潜在攻击面
            7. 防御建议
            """

            if self.ai_coordinator:
                result = await self.ai_coordinator.run('complex_reasoning', content=reverse_prompt)
                self.stats['reverse_engineering_sessions'] += 1
                return result
            else:
                return {"status": "error", "error": "AI协调器未启用"}

        except Exception as e:
            self.logger.error(f"逆向工程失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _optimize_strategy(self, target: str, **kwargs) -> Dict[str, Any]:
        """优化策略生成"""
        try:
            strategy_prompt = f"""
            为以下目标生成优化策略：
            目标: {target}
            当前状态: {kwargs.get('current_state', '未知')}
            优化目标: {kwargs.get('goal', '性能提升')}

            请生成：
            1. 现状分析
            2. 优化机会识别
            3. 具体优化措施
            4. 实施优先级
            5. 预期收益评估
            6. 风险评估
            """

            if self.ai_coordinator:
                result = await self.ai_coordinator.run('task_planning', content=strategy_prompt)
                return result
            else:
                return {"status": "error", "error": "AI协调器未启用"}

        except Exception as e:
            self.logger.error(f"策略优化失败: {e}")
            return {"status": "error", "error": str(e)}

    def _topological_sort(self, tasks: List[AgentTask]) -> List[AgentTask]:
        """拓扑排序任务"""
        # 简化的拓扑排序实现
        sorted_tasks = []
        visited = set()
        temp_visited = set()

        def visit(task):
            if task.task_id in temp_visited:
                return  # 循环依赖，跳过
            if task.task_id in visited:
                return

            temp_visited.add(task.task_id)

            # 访问依赖
            for dep_id in task.dependencies:
                dep_task = next((t for t in tasks if t.task_id == dep_id), None)
                if dep_task:
                    visit(dep_task)

            temp_visited.remove(task.task_id)
            visited.add(task.task_id)
            sorted_tasks.append(task)

        for task in tasks:
            if task.task_id not in visited:
                visit(task)

        return sorted_tasks

    def _check_dependencies(self, task: AgentTask, completed_tasks: List[str]) -> bool:
        """检查任务依赖"""
        return all(dep in completed_tasks for dep in task.dependencies)

    async def post_run(self, result: Dict[str, Any]) -> None:
        """后处理"""
        await super().post_run(result)

        # 更新统计信息
        self.stats['completed_tasks'] = len(self.completed_tasks)
        self.stats['failed_tasks'] = self.stats['total_tasks'] - self.stats['completed_tasks']

        # 计算平均执行时间
        execution_times = []
        for task in self.completed_tasks.values():
            if task.started_at and task.completed_at:
                execution_times.append(task.completed_at - task.started_at)

        if execution_times:
            self.stats['avg_execution_time'] = sum(execution_times) / len(execution_times)

        self.logger.info(f"🤖 AI代理执行完成 - 统计: {self.stats}")