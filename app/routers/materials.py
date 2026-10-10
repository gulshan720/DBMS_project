"""
Learning Materials Router
CRUD operations for course materials (videos, PDFs, articles).
"""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional
from app.services.mongo_service import get_collection, serialize_doc

router = APIRouter(prefix="/api/materials", tags=["Learning Materials"])

class MaterialCreate(BaseModel):
    material_id: str = Field(..., pattern=r"^M[0-9]{3,}$")
    course_id: str = Field(..., pattern=r"^C[0-9]{3,}$")
    title: str = Field(..., min_length=3)
    type: str = Field(..., pattern=r"^(video|pdf|article)$")
    content_url: str = Field(..., min_length=5)
    duration_minutes: Optional[int] = Field(15, ge=1)
    order_index: Optional[int] = 0

class MaterialUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = Field(None, pattern=r"^(video|pdf|article)$")
    content_url: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1)
    order_index: Optional[int] = None

@router.get("")
def list_materials(
    course_id: Optional[str] = Query(None, description="Filter by Course ID"),
    type: Optional[str] = Query(None, description="Filter by type (video, pdf, article)")
):
    """Retrieve learning materials with optional filters."""
    materials_col = get_collection("learning_materials")
    query = {}
    if course_id:
        query["course_id"] = course_id
    if type:
        query["type"] = type

    materials = list(materials_col.find(query).sort("order_index", 1))

    # Join course title
    courses_col = get_collection("courses")
    c_ids = list({m["course_id"] for m in materials if "course_id" in m})
    c_map = {c["course_id"]: c.get("title", "") for c in courses_col.find({"course_id": {"$in": c_ids}})}

    serialized = serialize_doc(materials)
    for m in serialized:
        m["course_title"] = c_map.get(m.get("course_id"), "N/A")

    return serialized

@router.get("/{material_id}")
def get_material(material_id: str):
    """Retrieve material by ID."""
    materials_col = get_collection("learning_materials")
    item = materials_col.find_one({"material_id": material_id})
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Material {material_id} not found")
    return serialize_doc(item)

@router.post("", status_code=status.HTTP_201_CREATED)
def create_material(payload: MaterialCreate):
    """Add a new learning material."""
    materials_col = get_collection("learning_materials")
    if materials_col.find_one({"material_id": payload.material_id}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Material ID '{payload.material_id}' already exists")

    courses_col = get_collection("courses")
    if not courses_col.find_one({"course_id": payload.course_id}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course '{payload.course_id}' does not exist")

    doc = payload.model_dump()
    try:
        materials_col.insert_one(doc)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Validation error: {str(e)}")

    return {"message": "Learning material created successfully", "material_id": payload.material_id}

@router.put("/{material_id}")
def update_material(material_id: str, payload: MaterialUpdate):
    """Update material details."""
    materials_col = get_collection("learning_materials")
    if not materials_col.find_one({"material_id": material_id}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Material {material_id} not found")

    update_fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_fields:
        return {"message": "No changes specified"}

    materials_col.update_one({"material_id": material_id}, {"$set": update_fields})
    return {"message": "Learning material updated successfully"}

@router.delete("/{material_id}")
def delete_material(material_id: str):
    """Delete a learning material."""
    materials_col = get_collection("learning_materials")
    res = materials_col.delete_one({"material_id": material_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Material {material_id} not found")
    return {"message": f"Material {material_id} deleted successfully"}
