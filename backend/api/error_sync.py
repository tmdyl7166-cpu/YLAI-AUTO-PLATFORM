from fastapi import APIRouter

router = APIRouter()

@router.post("/api/js-error")
async def js_error(payload: dict):
    # 统一结构化打印，便于 VS Code 终端查看
    print("\n✅ 前端 JS 错误同步到 VS Code：")
    print(payload)
    return {"status": "ok"}

@router.post("/api/js-console")
async def js_console(payload: dict):
    print("\n📦 浏览器 console 输出：")
    print(payload)
    return {"status": "ok"}
