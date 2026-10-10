"""
Quizzes and Progress Router
Management of quizzes, nested questions, student progress, and assessment scores.
"""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.services.mongo_service import get_collection, serialize_doc
from config.db_config import get_neo4j_driver
import neo4j_db.crud_operations as neo_crud

router = APIRouter(prefix="/api/quizzes", tags=["Quizzes & Progress"])

class QuestionItem(BaseModel):
    question_id: str
    question_text: str
    options: List[str]
    correct_answer: str
    points: int = 5

class QuizCreate(BaseModel):
    quiz_id: str = Field(..., pattern=r"^Q[0-9]{3,}$")
    course_id: str = Field(..., pattern=r"^C[0-9]{3,}$")
    title: str = Field(..., min_length=3)
    total_points: int = Field(..., ge=1)
    time_limit_minutes: Optional[int] = 15
    questions: List[QuestionItem]

class QuizUpdate(BaseModel):
    title: Optional[str] = None
    total_points: Optional[int] = Field(None, ge=1)
    time_limit_minutes: Optional[int] = Field(None, ge=1)
    questions: Optional[List[QuestionItem]] = None

class ProgressUpdate(BaseModel):
    completion_percentage: float = Field(..., ge=0, le=100)
    status: Optional[str] = None

class QuizScoreSubmit(BaseModel):
    quiz_id: str
    score: float = Field(..., ge=0)
    max_score: float = Field(..., ge=1)

@router.get("")
def list_quizzes(course_id: Optional[str] = Query(None, description="Filter by Course ID")):
    """List all quizzes."""
    quizzes_col = get_collection("quizzes")
    query = {"course_id": course_id} if course_id else {}
    quizzes = list(quizzes_col.find(query))

    # Join course title
    courses_col = get_collection("courses")
    c_ids = list({q["course_id"] for q in quizzes if "course_id" in q})
    c_map = {c["course_id"]: c.get("title", "") for c in courses_col.find({"course_id": {"$in": c_ids}})}

    serialized = serialize_doc(quizzes)
    for q in serialized:
        q["course_title"] = c_map.get(q.get("course_id"), "N/A")
        q["question_count"] = len(q.get("questions", []))

    return serialized

@router.get("/{quiz_id}")
def get_quiz_details(quiz_id: str):
    """Retrieve full quiz including questions."""
    quizzes_col = get_collection("quizzes")
    quiz = quizzes_col.find_one({"quiz_id": quiz_id})
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quiz {quiz_id} not found")
    return serialize_doc(quiz)

@router.post("", status_code=status.HTTP_201_CREATED)
def create_quiz(payload: QuizCreate):
    """Create a new quiz with embedded questions."""
    quizzes_col = get_collection("quizzes")
    if quizzes_col.find_one({"quiz_id": payload.quiz_id}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Quiz ID '{payload.quiz_id}' already exists")

    courses_col = get_collection("courses")
    if not courses_col.find_one({"course_id": payload.course_id}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course '{payload.course_id}' not found")

    doc = payload.model_dump()
    quizzes_col.insert_one(doc)
    return {"message": "Quiz created successfully", "quiz_id": payload.quiz_id}

@router.put("/{quiz_id}")
def update_quiz(quiz_id: str, payload: QuizUpdate):
    """Update quiz attributes."""
    quizzes_col = get_collection("quizzes")
    existing = quizzes_col.find_one({"quiz_id": quiz_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quiz {quiz_id} not found")

    update_fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_fields:
        return {"message": "No changes specified"}

    quizzes_col.update_one({"quiz_id": quiz_id}, {"$set": update_fields})
    return {"message": f"Quiz {quiz_id} updated successfully", "updated_fields": list(update_fields.keys())}

@router.delete("/{quiz_id}")
def delete_quiz(quiz_id: str):
    """Delete a quiz."""
    quizzes_col = get_collection("quizzes")
    res = quizzes_col.delete_one({"quiz_id": quiz_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quiz {quiz_id} not found")
    return {"message": f"Quiz {quiz_id} deleted successfully"}

# ── Progress Endpoints ────────────────────────────────────────────────────────

@router.get("/progress/all")
def list_progress_records(
    student_id: Optional[str] = Query(None),
    course_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status")
):
    """List student progress records with course and student metadata."""
    progress_col = get_collection("progress")
    query = {}
    if student_id:
        query["student_id"] = student_id
    if course_id:
        query["course_id"] = course_id
    if status_filter:
        query["status"] = status_filter

    pipeline = [
        {"$match": query},
        {"$lookup": {"from": "students", "localField": "student_id", "foreignField": "student_id", "as": "student"}},
        {"$lookup": {"from": "courses", "localField": "course_id", "foreignField": "course_id", "as": "course"}},
        {"$unwind": {"path": "$student", "preserveNullAndEmptyArrays": True}},
        {"$unwind": {"path": "$course", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "progress_id": 1,
            "student_id": 1,
            "student_name": "$student.name",
            "course_id": 1,
            "course_title": "$course.title",
            "completion_percentage": 1,
            "status": 1,
            "last_accessed": 1,
            "quiz_scores": 1
        }},
        {"$sort": {"last_accessed": -1}}
    ]

    records = list(progress_col.aggregate(pipeline))
    return serialize_doc(records)

@router.put("/progress/{student_id}/{course_id}")
def update_student_progress(student_id: str, course_id: str, payload: ProgressUpdate):
    """Update progress percentage and completion status for a student."""
    progress_col = get_collection("progress")
    rec = progress_col.find_one({"student_id": student_id, "course_id": course_id})
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress record not found")

    new_status = payload.status
    if not new_status:
        new_status = "completed" if payload.completion_percentage >= 100 else "in_progress"

    progress_col.update_one(
        {"student_id": student_id, "course_id": course_id},
        {"$set": {
            "completion_percentage": payload.completion_percentage,
            "status": new_status,
            "last_accessed": datetime.now()
        }}
    )

    # If completed, reflect in Neo4j as COMPLETED relationship
    if new_status == "completed":
        try:
            driver = get_neo4j_driver()
            neo_crud.mark_course_completed(
                driver,
                student_id=student_id,
                course_id=course_id,
                completion_date=datetime.now().strftime("%Y-%m-%d"),
                grade="A"
            )
        except Exception:
            pass

    return {
        "message": f"Progress updated for {student_id} in {course_id}",
        "completion_percentage": payload.completion_percentage,
        "status": new_status
    }

@router.post("/progress/{student_id}/{course_id}/score")
def record_quiz_score(student_id: str, course_id: str, payload: QuizScoreSubmit):
    """Record a quiz attempt score into student progress."""
    progress_col = get_collection("progress")
    rec = progress_col.find_one({"student_id": student_id, "course_id": course_id})
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress record not found")

    score_item = {
        "quiz_id": payload.quiz_id,
        "score": payload.score,
        "max_score": payload.max_score,
        "attempt_date": datetime.now()
    }

    progress_col.update_one(
        {"student_id": student_id, "course_id": course_id},
        {
            "$push": {"quiz_scores": score_item},
            "$set": {"last_accessed": datetime.now()}
        }
    )

    return {"message": "Quiz score recorded successfully", "attempt": serialize_doc(score_item)}

@router.delete("/progress/{student_id}/{course_id}")
def delete_progress(student_id: str, course_id: str):
    """Delete a student progress record."""
    progress_col = get_collection("progress")
    res = progress_col.delete_one({"student_id": student_id, "course_id": course_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress record not found")
    return {"message": f"Progress record for {student_id} in {course_id} deleted successfully"}
