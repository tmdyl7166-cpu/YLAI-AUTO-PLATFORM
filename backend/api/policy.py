from fastapi import APIRouter, Depends
from backend.api.auth import require_perm
from backend.core.policy import GlobalPolicy, POLICY_PATH
import yaml

router = APIRouter()


@router.get("/api/policy/get")
@router.get("/api/policy/get")
def get_policy(_auth=Depends(require_perm("view"))):
    return {"code": 0, "data": GlobalPolicy.load()}


@router.post("/api/policy/set")
@router.post("/api/policy/set")
def set_policy(data: dict, _auth=Depends(require_perm("maintain"))):
    cfg = GlobalPolicy.load()
    level = int(data.get("level", cfg.get("policy_level", 0)))
    cfg["policy_level"] = level

    with open(POLICY_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)

    GlobalPolicy._cache = None
    return {"code": 0, "level": level}