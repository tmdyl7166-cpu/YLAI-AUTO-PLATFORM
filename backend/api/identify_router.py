from fastapi import APIRouter
router = APIRouter()
@router.get("/api/identify/")
async def identify_status():
    return {"status": "not implemented"}
