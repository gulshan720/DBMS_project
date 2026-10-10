"""
Dashboard Router
Aggregates high-level metrics and statistics from MongoDB and Neo4j.
"""

from fastapi import APIRouter
from app.services.mongo_service import get_collection, serialize_doc
from app.services.neo4j_service import get_graph_counts

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_dashboard_stats():
    """Retrieve comprehensive portal metrics from MongoDB and Neo4j."""
    # MongoDB collection counts
    students_col = get_collection("students")
    courses_col = get_collection("courses")
    instructors_col = get_collection("instructors")
    materials_col = get_collection("learning_materials")
    quizzes_col = get_collection("quizzes")
    progress_col = get_collection("progress")

    mongo_counts = {
        "students": students_col.count_documents({}),
        "courses": courses_col.count_documents({}),
        "instructors": instructors_col.count_documents({}),
        "learning_materials": materials_col.count_documents({}),
        "quizzes": quizzes_col.count_documents({}),
        "progress_records": progress_col.count_documents({})
    }

    # Progress breakdown
    completed_count = progress_col.count_documents({"status": "completed"})
    in_progress_count = progress_col.count_documents({"status": {"$in": ["in_progress", "enrolled"]}})
    
    # Calculate overall avg completion
    avg_pipeline = [
        {"$group": {"_id": None, "overall_avg": {"$avg": "$completion_percentage"}}}
    ]
    avg_res = list(progress_col.aggregate(avg_pipeline))
    overall_avg = round(avg_res[0]["overall_avg"], 1) if avg_res and "overall_avg" in avg_res[0] else 0.0

    # Neo4j graph counts
    graph_counts = get_graph_counts()

    # Recent progress entries with student & course details
    recent_pipeline = [
        {"$sort": {"last_accessed": -1}},
        {"$limit": 6},
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
            "_id": 0
        }}
    ]
    recent_activity = serialize_doc(list(progress_col.aggregate(recent_pipeline)))

    return {
        "mongodb": {
            "counts": mongo_counts,
            "progress_summary": {
                "completed": completed_count,
                "in_progress": in_progress_count,
                "overall_average_completion": overall_avg
            }
        },
        "neo4j": graph_counts,
        "recent_activity": recent_activity
    }
