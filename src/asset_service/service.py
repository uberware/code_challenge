"""
FastAPI microservice application.
"""

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
    return {"status": "success", "asset": {"name": name, "asset_type": asset_type}}


@router.get("/list", description="List Assets that match criteria")
async def list_assets(
    name: str | None = None, asset_type: str | None = None, registry: str | None = None
):
    """List assets that match criteria."""
    reg = db.AssetRegistry(registry)
    # TODO: this may not be the best asynchronous way to build the list
    result = list(api.list_assets(name, asset_type, registry=reg))
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No Assets found: name='{name or ''}' asset_type='{asset_type or ''}'",
        )
    return {"status": "success", "assets": result}


@router.post("/versions/add", description="Add a single version")
async def add_version(req: VersionReq):
    """Add a version."""
    reg = db.AssetRegistry(req.registry)
    asset = api.add_asset(req.name, req.asset_type, registry=reg)
    if not asset:
        raise HTTPException(status_code=422, detail=f"Asset failed validation: {req}")
    if not api.add_asset_version(
        asset, req.department, req.version, req.status, registry=reg
    ):
        raise HTTPException(status_code=422, detail=f"Version failed validation: {req}")
    return {"status": "success", "message": f"Added version: {req}"}


@router.get(
    "/versions/get/{name}/{asset_type}/{department}/{version}",
    description="Get a specific version",
)
async def get_version(
    name: str,
    asset_type: str,
    department: str,
    version: int,
    registry: str | None = None,
):
    """Get a specific version."""
    reg = db.AssetRegistry(registry)
    result = api.get_asset_version(name, asset_type, department, version, registry=reg)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Version not found: {name}/{asset_type} - {department}:{version}",
        )
    return {
        "status": "success",
        "version": {
            "name": name,
            "asset_type": asset_type,
            "department": department,
            "version": version,
            "status": result.state.status,
        },
    }


@router.get("/versions/list/{name}/{asset_type}", description="List versions")
async def list_versions(
    name: str,
    asset_type: str,
    department: str | None = None,
    version: int | None = None,
    status: str | None = None,
    registry: str | None = None,
):
    """List versions of a specific asset."""
    reg = db.AssetRegistry(registry)
    # TODO: this may not be the best asynchronous way to build the list
    result = []
    for item in api.list_asset_versions(
        name, asset_type, department, version, status, registry=reg
    ):
        # convert to the original data format
        result.append(
            {
                "asset": {
                    "name": item.key.asset.name,
                    "asset_type": item.key.asset.asset_type,
                },
                "department": item.key.department,
                "version": item.key.version,
                "status": item.state.status,
            }
        )
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No Versions found: {name}/{asset_type} filters: {department} {version} {status}",
        )
    return {"status": "success", "versions": result}


@router.get(
    "/versions/latest/{name}/{asset_type}/{department}", description="Latest version"
)
async def get_latest_version(
    name: str,
    asset_type: str,
    department: str,
    active_only: bool = True,
    registry: str | None = None,
):
    """Latest version of a specific asset."""
    reg = db.AssetRegistry(registry)
    result = api.get_latest_version(
        name, asset_type, department, active_only, registry=reg
    )
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No versions found: {name}/{asset_type} - {department} active_only={active_only}",
        )
    return {
        "status": "success",
        "version": result.key.version,
    }


app = FastAPI()
app.include_router(router, prefix="/v1")
