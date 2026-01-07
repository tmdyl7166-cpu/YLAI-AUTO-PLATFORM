from pathlib import Path
from config import WATCH_DIRS, POLL_INTERVAL, AUTO_FIX
import json
import threading
import uvicorn
import asyncio
import os
import sys

# 获取项目根目录
ROOT = Path(__file__).resolve().parents[1]

# 添加backend路径
sys.path.append(str(ROOT / 'backend'))

from orchestrator import run_pipeline_on_dirs
from trainer import save_training_sample
from backend.scripts.ai_coordinator import AIModelCoordinator
import time

DATA_FILE = ROOT / "data" / "results.json"

print("✅ AI 多模型联动自动编排系统已启动")
print("🎯 模型功能分配：")
print("  📝 qwen3:8b     - 中文内容理解与分析")
print("  🧠 llama3.1:8b  - 任务规划与指令理解")
print("  🤔 deepseek-r1:8b - 复杂推理与决策制定")
print("  🎨 gpt-oss:20b  - 创意生成与文本优化")

# 初始化AI协调器
ai_coordinator = None

async def init_ai_coordinator():
    """初始化AI协调器"""
    global ai_coordinator
    try:
        ai_coordinator = AIModelCoordinator()
        await ai_coordinator.initialize()
        print("✅ AI协调器初始化成功")
    except Exception as e:
        print(f"❌ AI协调器初始化失败: {e}")
        ai_coordinator = None

def start_web_console():
    try:
        uvicorn.run("web_console:app", host="0.0.0.0", port=9001, log_level="info")
    except Exception as e:
        print("[web-console] start failed:", e)

async def enhanced_pipeline():
    """增强的处理管道，集成AI联动"""
    while True:
        try:
            # 基础处理
            summary = run_pipeline_on_dirs(WATCH_DIRS, auto_fix=AUTO_FIX)

            # 如果AI协调器可用，进行智能增强
            if ai_coordinator:
                enhanced_summary = await enhance_with_ai_coordination(summary)
                summary = enhanced_summary

            # 保存结果
            DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            DATA_FILE.write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")

            # 记录训练样本
            for item in summary.get("items", []):
                if item.get("status") == "optimized":
                    save_training_sample(
                        item.get("file"),
                        "",
                        "",
                        item.get("stages", []),
                    )

        except Exception as e:
            print(f"处理管道错误: {e}")

        await asyncio.sleep(POLL_INTERVAL)

async def enhance_with_ai_coordination(summary):
    """使用AI协调器增强处理结果"""
    try:
        enhanced_items = []

        for item in summary.get("items", []):
            if item.get("status") == "needs_review":
                # 对需要审查的项目进行AI分析
                analysis_result = await ai_coordinator.run(
                    'analyze_content',
                    content=f"文件: {item.get('file')}\n问题: {item.get('issues', [])}\n建议: {item.get('suggestions', [])}"
                )

                if analysis_result.get('status') == 'success':
                    item['ai_analysis'] = analysis_result['result']
                    item['ai_enhanced'] = True

                    # 如果AI认为可以自动修复
                    if 'auto_fix_recommended' in analysis_result.get('result', {}):
                        item['status'] = 'ai_optimized'

            enhanced_items.append(item)

        summary['items'] = enhanced_items
        summary['ai_enhanced'] = True
        summary['ai_models_used'] = await get_ai_model_status()

        return summary

    except Exception as e:
        print(f"AI增强处理失败: {e}")
        return summary

async def get_ai_model_status():
    """获取AI模型状态"""
    if ai_coordinator:
        try:
            status = await ai_coordinator.run('get_model_status')
            return status.get('models', {})
        except Exception as e:
            print(f"获取模型状态失败: {e}")
    return {}

async def main():
    """主函数"""
    # 初始化AI协调器
    await init_ai_coordinator()

    # 启动Web控制台
    console_thread = threading.Thread(target=start_web_console, daemon=True)
    console_thread.start()

    # 启动增强处理管道
    await enhanced_pipeline()

if __name__ == "__main__":
    asyncio.run(main())
