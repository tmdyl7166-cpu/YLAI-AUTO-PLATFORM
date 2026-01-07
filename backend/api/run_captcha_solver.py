from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/api/captcha/solve")
async def run_captcha_solver(request: Request):
    """
    集成OCR库自动识别验证码
    """
    # TODO: 实现验证码识别逻辑
    return {"status": "pending", "msg": "验证码识别功能待实现"}
