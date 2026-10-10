"""
Students Router
CRUD operations and enrollment management for Student documents.
"""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.services.mongo_service import get_collection, serialize_doc
from config.db_config import get_neo4j_driver
import neo4j_db.crud_operations as neo_crud

router = APIRouter(prefix="/api/students", tags=["Students"])

class StudentCreate(BaseModel):
    student_id: str = Field(..., pattern=r"^S[0-9]{3,}$")
    name: str = Field(..., min_length=2)
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: str = Field(..., min_length=7, max_length=15)
    enrollment_date: Optional[str] = None
    courses_enrolled: Optional[List[str]] = []

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = Field(None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: Optional[str] = None

class EnrollRequest(BaseModel):
    course_id: str

@router.get("")
def list_students(
    search: Optional[str] = Query(None, description="Search by name, email, or student_id"),
    limit: int = Query(50, ge=1, le=100)
):
    """Retrieve students with optional search filter."""
    students_col = get_collection("students")
    query = {}
    if search:
        regex = {"$regex": search.strip(), "$options": "i"}
        query = {"$or": [{"student_id": regex}, {"name": regex}, {"email": regex}]}
    
    docs = list(students_col.find(query).limit(limit))
    return serialize_doc(docs)

@router.get("/{student_id}")
def get_student_details(student_id: str):
    """Retrieve full details of a student including progress and Neo4j skills."""
    students_col = get_collection("students")
    student = students_col.find_one({"student_id": student_id})
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student {student_id} not found")

    # Fetch progress records for student
    progress_col = get_collection("progress")
    progress_records = list(progress_col.find({"student_id": student_id}))

    # Enrich with course titles
    courses_col = get_collection("courses")
    enrolled_cids = student.get("courses_enrolled", [])
    courses_info = list(courses_col.find({"course_id": {"$in": enrolled_cids}}, {"_id": 0}))

    # Optional Neo4j skills lookup
    skills = []
    try:
        driver = get_neo4j_driver()
        with driver.session() as s:
            res = s.run(
                "MATCH (st:Student {student_id: $sid})-[r:HAS_SKILL]->(sk:Skill) "
                "RETURN sk.skill_id AS id, sk.name AS name, r.proficiency_level AS proficiency",
                sid=student_id
            )
            skills = [dict(record) for record in res]
    except Exception:
        pass

    return {
        "student": serialize_doc(student),
        "courses": serialize_doc(courses_info),
        "progress": serialize_doc(progress_records),
        "skills": skills
    }

@router.post("", status_code=status.HTTP_201_CREATED)
def create_student(payload: StudentCreate):
    """Create a new student in MongoDB and synchronize to Neo4j."""
    students_col = get_collection("students")
    
    # Check duplicate ID
    if students_col.find_one({"student_id": payload.student_id}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student with ID '{payload.student_id}' already exists."
        )

    # Check duplicate email
    if students_col.find_one({"email": payload.email}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student with email '{payload.email}' already exists."
        )

    doc = {
        "student_id": payload.student_id,
        "name": payload.name,
        "email": payload.email,
        "phone": payload.phone,
        "enrollment_date": datetime.fromisoformat(payload.enrollment_date) if payload.enrollment_date else datetime.now(),
        "courses_enrolled": payload.courses_enrolled or []
    }

    try:
        students_col.insert_one(doc)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Database validation error: {str(e)}")

    # Sync to Neo4j
    try:
        driver = get_neo4j_driver()
        neo_crud.create_student(
            driver,
            student_id=payload.student_id,
            name=payload.name,
            email=payload.email,
            enrollment_date=doc["enrollment_date"].strftime("%Y-%m-%d")
        )
    except Exception:
        pass  # Non-fatal if Neo4j sync encounters warning

    return {"message": "Student created successfully", "student_id": payload.student_id}

@router.put("/{student_id}")
def update_student(student_id: str, payload: StudentUpdate):
    """Update student attributes."""
    students_col = get_collection("students")
    existing = students_col.find_one({"student_id": student_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student {student_id} not found")

    update_fields = {}
    if payload.name is not None:
        update_fields["name"] = payload.name
    if payload.email is not None:
        # Check if email taken by someone else
        duplicate = students_col.find_one({"email": payload.email, "student_id": {"$ne": student_id}})
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use by another student")
        update_fields["email"] = payload.email
    if payload.phone is not None:
        update_fields["phone"] = payload.phone

    if not update_fields:
        return {"message": "No changes specified"}

    students_col.update_one({"student_id": student_id}, {"$set": update_fields})

    # Update Neo4j if email changed
    if "email" in update_fields:
        try:
            driver = get_neo4j_driver()
            neo_crud.update_student_email(driver, student_id, update_fields["email"])
        except Exception:
            pass

    return {"message": "Student updated successfully", "updated_fields": list(update_fields.keys())}

@router.delete("/{student_id}")
def delete_student(student_id: str):
    """Delete student record and remove in Neo4j."""
    students_col = get_collection("students")
    res = students_col.delete_one({"student_id": student_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student {student_id} not found")

    # Clean up progress records in MongoDB
    get_collection("progress").delete_many({"student_id": student_id})

    # Clean up in Neo4j
    try:
        driver = get_neo4j_driver()
        neo_crud.delete_student(driver, student_id)
    except Exception:
        pass

    return {"message": f"Student {student_id} and associated progress records deleted successfully"}

@router.post("/{student_id}/enroll")
def enroll_student_course(student_id: str, payload: EnrollRequest):
    """Enroll student in a course atomically."""
    students_col = get_collection("students")
    courses_col = get_collection("courses")
    progress_col = get_collection("progress")

    student = students_col.find_one({"student_id": student_id})
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    course = courses_col.find_one({"course_id": payload.course_id})
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # Atomically update MongoDB student
    students_col.update_one(
        {"student_id": student_id},
        {"$addToSet": {"courses_enrolled": payload.course_id}}
    )

    # Create progress document if not existing
    pid = f"P_{student_id}_{payload.course_id}"
    existing_p = progress_col.find_one({"student_id": student_id, "course_id": payload.course_id})
    if not existing_p:
        progress_col.insert_one({
            "progress_id": pid,
            "student_id": student_id,
            "course_id": payload.course_id,
            "completion_percentage": 0,
            "status": "in_progress",
            "last_accessed": datetime.now(),
            "quiz_scores": []
        })

    # Sync to Neo4j
    try:
        driver = get_neo4j_driver()
        neo_crud.create_enrollment(driver, student_id, payload.course_id)
    except Exception:
        pass

    return {"message": f"Student {student_id} successfully enrolled in {course['title']} ({payload.course_id})"}
