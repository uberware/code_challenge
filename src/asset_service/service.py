"""FastAPI microservice application."""

from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel

from asset_service import api, db


class BaseReq(BaseModel):
    """Base model for all posts."""

    registry: str | None = None


class FileReq(BaseReq):
    """Request model for file upload."""

    filename: Path


class AssetReq(BaseReq):
    """Request model for asset upload."""

    name: str
    asset_type: str


class VersionReq(AssetReq):
    """Request model for asset version upload."""

    department: str
    version: int
    status: str


router = APIRouter()


@router.post("/load", description="Load assets from a JSON file")
async def load(req: FileReq):
    """Load from a json file."""
    if not req.filename.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {req.filename}")
    if not api.load_from_json(req.filename, registry=db.AssetRegistry(req.registry)):
        raise HTTPException(
            status_code=422, detail=f"File failed validation: {req.filename}"
        )
    return {"status": "success", "message": f"Loaded assets from: {req.filename}"}


@router.post("/add", description="Add a single asset")
async def add_asset(req: AssetReq):
    """Add an asset."""
    if not api.add_asset(
        req.name, req.asset_type, registry=db.AssetRegistry(req.registry)
    ):
        raise HTTPException(status_code=422, detail=f"Asset failed validation: {req}")
    return {"status": "success", "message": f"Added asset: {req}"}


@router.get("/get/{name}/{asset_type}", description="Get a specific asset")
async def get_asset(name: str, asset_type: str, registry: str | None = None):
    """Get a specific asset."""
    reg = db.AssetRegistry(registry)
    if not api.get_asset(name, asset_type, registry=reg):
        raise HTTPException(
            status_code=404, detail=f"Asset not found: {name}/{asset_type}"
        )
    return {"status": "success", "message": f"Found Asset: {name}/{asset_type}"}


@router.post("/versions/add", description="Add a single version")
async def add_version(req: VersionReq):
    """Add a version."""
    reg = db.AssetRegistry(req.registry)
    asset = api.add_asset(req.name, req.asset_type, registry=reg)
    if not asset:
        raise HTTPException(status_code=422, detail=f"Asset failed validation: {req}")
    if not api.add_version(
        asset, req.department, req.version, req.status, registry=reg
    ):
        raise HTTPException(status_code=422, detail=f"Version failed validation: {req}")
    return {"status": "success", "message": f"Added version: {req}"}


app = FastAPI()
app.include_router(router, prefix="/v1")
