"""
Courses Router
CRUD operations and catalog exploration for Course documents.
"""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.services.mongo_service import get_collection, serialize_doc
from config.db_config import get_neo4j_driver
import neo4j_db.graph_traversal as neo_traversal

router = APIRouter(prefix="/api/courses", tags=["Courses"])

class CourseCreate(BaseModel):
    course_id: str = Field(..., pattern=r"^C[0-9]{3,}$")
    title: str = Field(..., min_length=3)
    description: Optional[str] = "Course curriculum overview"
    category: str = Field(..., min_length=2)
    difficulty_level: str = Field(..., pattern=r"^(Beginner|Intermediate|Advanced)$")
    instructor_id: str = Field(..., pattern=r"^I[0-9]{3,}$")
    duration_hours: int = Field(..., ge=1)
    price: float = Field(..., ge=0)

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty_level: Optional[str] = Field(None, pattern=r"^(Beginner|Intermediate|Advanced)$")
    instructor_id: Optional[str] = None
    duration_hours: Optional[int] = Field(None, ge=1)
    price: Optional[float] = Field(None, ge=0)

@router.get("")
def list_courses(
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    search: Optional[str] = Query(None, description="Search by title or course_id")
):
    """Retrieve courses with optional category, difficulty, and search filters."""
    courses_col = get_collection("courses")
    query = {}
    if category:
        query["category"] = category
    if difficulty:
        query["difficulty_level"] = difficulty
    if search:
        regex = {"$regex": search.strip(), "$options": "i"}
        query["$or"] = [{"course_id": regex}, {"title": regex}, {"category": regex}]

    courses = list(courses_col.find(query))

    # Join instructor names
    instructors_col = get_collection("instructors")
    inst_ids = list({c["instructor_id"] for c in courses if "instructor_id" in c})
    inst_map = {
        i["instructor_id"]: i.get("name", "Unknown")
        for i in instructors_col.find({"instructor_id": {"$in": inst_ids}})
    }

    serialized = serialize_doc(courses)
    for c in serialized:
        c["instructor_name"] = inst_map.get(c.get("instructor_id"), "N/A")

    return serialized

@router.get("/meta")
def get_course_metadata():
    """Retrieve distinct categories and difficulty levels."""
    courses_col = get_collection("courses")
    categories = courses_col.distinct("category")
    instructors_col = get_collection("instructors")
    instructors = list(instructors_col.find({}, {"_id": 0, "instructor_id": 1, "name": 1, "specialization": 1}))
    return {
        "categories": categories,
        "difficulties": ["Beginner", "Intermediate", "Advanced"],
        "instructors": serialize_doc(instructors)
    }

@router.get("/{course_id}")
def get_course_details(course_id: str):
    """Retrieve full course details including materials, quizzes, and prerequisites."""
    courses_col = get_collection("courses")
    course = courses_col.find_one({"course_id": course_id})
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course {course_id} not found")

    # Instructor details
    instructors_col = get_collection("instructors")
    instructor = instructors_col.find_one({"instructor_id": course.get("instructor_id")}, {"_id": 0})

    # Learning Materials
    materials_col = get_collection("learning_materials")
    materials = list(materials_col.find({"course_id": course_id}).sort("order_index", 1))

    # Quizzes
    quizzes_col = get_collection("quizzes")
    quizzes = list(quizzes_col.find({"course_id": course_id}))

    # Neo4j Prerequisites
    prereqs = []
    try:
        driver = get_neo4j_driver()
        prereqs = neo_traversal.find_course_prerequisites(driver, course_id)
    except Exception:
        pass

    return {
        "course": serialize_doc(course),
        "instructor": serialize_doc(instructor),
        "materials": serialize_doc(materials),
        "quizzes": serialize_doc(quizzes),
        "prerequisites": prereqs
    }

@router.post("", status_code=status.HTTP_201_CREATED)
def create_course(payload: CourseCreate):
    """Create a new course in MongoDB and synchronize to Neo4j."""
    courses_col = get_collection("courses")
    if courses_col.find_one({"course_id": payload.course_id}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Course ID '{payload.course_id}' already exists")

    doc = {
        "course_id": payload.course_id,
        "title": payload.title,
        "description": payload.description or "Comprehensive course",
        "category": payload.category,
        "difficulty_level": payload.difficulty_level,
        "instructor_id": payload.instructor_id,
        "duration_hours": payload.duration_hours,
        "price": payload.price,
        "created_date": datetime.now()
    }

    try:
        courses_col.insert_one(doc)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Schema validation error: {str(e)}")

    # Sync to Neo4j
    try:
        driver = get_neo4j_driver()
        with driver.session() as s:
            s.run(
                "MERGE (c:Course {course_id: $cid}) "
                "SET c.title = $title, c.category = $cat, c.difficulty_level = $diff, "
                "    c.duration_hours = $dur, c.price = $price",
                cid=payload.course_id, title=payload.title, cat=payload.category,
                diff=payload.difficulty_level, dur=payload.duration_hours, price=payload.price
            )
            # Link to Category
            s.run(
                "MERGE (cat:Category {name: $cat}) "
                "WITH cat "
                "MATCH (c:Course {course_id: $cid}) "
                "MERGE (c)-[:BELONGS_TO]->(cat)",
                cat=payload.category, cid=payload.course_id
            )
            # Link to Instructor
            s.run(
                "MATCH (i:Instructor {instructor_id: $iid}), (c:Course {course_id: $cid}) "
                "MERGE (i)-[:TEACHES {since: date()}]->(c)",
                iid=payload.instructor_id, cid=payload.course_id
            )
    except Exception:
        pass

    return {"message": "Course created successfully", "course_id": payload.course_id}

@router.put("/{course_id}")
def update_course(course_id: str, payload: CourseUpdate):
    """Update course attributes."""
    courses_col = get_collection("courses")
    existing = courses_col.find_one({"course_id": course_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course {course_id} not found")

    update_fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_fields:
        return {"message": "No changes specified"}

    courses_col.update_one({"course_id": course_id}, {"$set": update_fields})

    # Sync to Neo4j
    try:
        driver = get_neo4j_driver()
        with driver.session() as s:
            s.run(
                "MATCH (c:Course {course_id: $cid}) "
                "SET c.title = coalesce($title, c.title), "
                "    c.category = coalesce($cat, c.category), "
                "    c.difficulty_level = coalesce($diff, c.difficulty_level), "
                "    c.price = coalesce($price, c.price)",
                cid=course_id,
                title=update_fields.get("title"),
                cat=update_fields.get("category"),
                diff=update_fields.get("difficulty_level"),
                price=update_fields.get("price")
            )
    except Exception:
        pass

    return {"message": "Course updated successfully", "updated_fields": list(update_fields.keys())}

@router.delete("/{course_id}")
def delete_course(course_id: str):
    """Delete course and associated materials/quizzes."""
    courses_col = get_collection("courses")
    res = courses_col.delete_one({"course_id": course_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course {course_id} not found")

    # Cascade deletes to materials, quizzes, progress, and student enrollments
    get_collection("learning_materials").delete_many({"course_id": course_id})
    get_collection("quizzes").delete_many({"course_id": course_id})
    get_collection("progress").delete_many({"course_id": course_id})
    get_collection("students").update_many({}, {"$pull": {"courses_enrolled": course_id}})

    # Detach delete in Neo4j
    try:
        driver = get_neo4j_driver()
        with driver.session() as s:
            s.run("MATCH (c:Course {course_id: $cid}) DETACH DELETE c", cid=course_id)
    except Exception:
        pass

    return {"message": f"Course {course_id} and related materials/quizzes deleted"}
