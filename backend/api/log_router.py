from fastapi import APIRouter
router = APIRouter()
@router.get("/api/log/")
async def log_status():
    return {"status": "not implemented"}
