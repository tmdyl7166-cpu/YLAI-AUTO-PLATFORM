from fastapi import APIRouter
router = APIRouter()
@router.get("/api/param/")
async def param_status():
    return {"status": "not implemented"}
