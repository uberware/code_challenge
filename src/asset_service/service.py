"""FastAPI microservice application."""

from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel

from asset_service import api

class FileRequest(BaseModel):
    """Request model for file upload."""

    filename: Path


router = APIRouter()


@router.get("/")
async def get_root():
    """Root handler."""
    return {"message": "Could have documentation here."}


@router.post("/load", description="Load assets from a JSON file")
async def load(payload: FileRequest):
    """Load from a json file."""
    if not payload.filename.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {payload.filename}")
    if not api.load_from_json(payload.filename):
        raise HTTPException(status_code=422, detail=f"File failed validation: {payload.filename}")
    return {"status": "success", "message": f"Loaded assets from: {payload.filename}"}


app = FastAPI()
app.include_router(router, prefix="/v1")
