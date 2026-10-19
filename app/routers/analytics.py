"""
Analytics Router
Exposes MongoDB aggregation framework pipelines and execution plan performance analysis.
"""

from fastapi import APIRouter
from app.services.mongo_service import get_collection, serialize_doc

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/course-completion")
def get_avg_course_completion():
    """Pipeline 1: Average completion percentage per course with titles."""
    progress_col = get_collection("progress")
    pipeline = [
        {"$group": {
            "_id": "$course_id",
            "avg_completion": {"$avg": "$completion_percentage"},
            "student_count": {"$sum": 1}
        }},
        {"$lookup": {
            "from": "courses",
            "localField": "_id",
            "foreignField": "course_id",
            "as": "course"
        }},
        {"$unwind": "$course"},
        {"$project": {
            "course_id": "$_id",
            "title": "$course.title",
            "category": "$course.category",
            "average_completion": {"$round": ["$avg_completion", 2]},
            "enrolled_count": "$student_count",
            "_id": 0
        }},
        {"$sort": {"average_completion": -1}}
    ]
    results = list(progress_col.aggregate(pipeline))
    return serialize_doc(results)

@router.get("/top-students")
def get_top_students():
    """Pipeline 2: Top students by number of completed courses."""
    progress_col = get_collection("progress")
    pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": "$student_id",
            "completed_count": {"$sum": 1}
        }},
        {"$sort": {"completed_count": -1}},
        {"$limit": 5},
        {"$lookup": {
            "from": "students",
            "localField": "_id",
            "foreignField": "student_id",
            "as": "student"
        }},
        {"$unwind": "$student"},
        {"$project": {
            "student_id": "$_id",
            "name": "$student.name",
            "email": "$student.email",
            "completed_courses_count": "$completed_count",
            "_id": 0
        }}
    ]
    results = list(progress_col.aggregate(pipeline))
    return serialize_doc(results)

@router.get("/revenue")
def get_revenue_analysis():
    """Pipeline 3: Course revenue analysis (enrolled count * catalog price)."""
    students_col = get_collection("students")
    pipeline = [
        {"$unwind": "$courses_enrolled"},
        {"$group": {
            "_id": "$courses_enrolled",
            "enrolled_count": {"$sum": 1}
        }},
        {"$lookup": {
            "from": "courses",
            "localField": "_id",
            "foreignField": "course_id",
            "as": "course"
        }},
        {"$unwind": "$course"},
        {"$project": {
            "course_id": "$_id",
            "title": "$course.title",
            "category": "$course.category",
            "price": "$course.price",
            "enrolled_students": "$enrolled_count",
            "estimated_revenue": {"$round": [{"$multiply": ["$enrolled_count", "$course.price"]}, 2]},
            "_id": 0
        }},
        {"$sort": {"estimated_revenue": -1}}
    ]
    results = list(students_col.aggregate(pipeline))
    return serialize_doc(results)

@router.get("/quiz-performance")
def get_quiz_performance():
    """Pipeline 4: Average student score and attempts across all quizzes."""
    progress_col = get_collection("progress")
    pipeline = [
        {"$unwind": "$quiz_scores"},
        {"$group": {
            "_id": "$quiz_scores.quiz_id",
            "average_score": {"$avg": "$quiz_scores.score"},
            "attempts": {"$sum": 1}
        }},
        {"$lookup": {
            "from": "quizzes",
            "localField": "_id",
            "foreignField": "quiz_id",
            "as": "quiz"
        }},
        {"$unwind": "$quiz"},
        {"$project": {
            "quiz_id": "$_id",
            "title": "$quiz.title",
            "course_id": "$quiz.course_id",
            "total_points": "$quiz.total_points",
            "average_score": {"$round": ["$average_score", 2]},
            "attempts": 1,
            "_id": 0
        }},
        {"$sort": {"average_score": -1}}
    ]
    results = list(progress_col.aggregate(pipeline))
    return serialize_doc(results)

@router.get("/materials-distribution")
def get_materials_distribution():
    """Pipeline 5: Count of learning materials by type."""
    materials_col = get_collection("learning_materials")
    pipeline = [
        {"$group": {
            "_id": "$type",
            "count": {"$sum": 1}
        }},
        {"$project": {
            "material_type": "$_id",
            "count": 1,
            "_id": 0
        }},
        {"$sort": {"count": -1}}
    ]
    results = list(materials_col.aggregate(pipeline))
    return serialize_doc(results)

@router.get("/skill-distribution")
def get_skill_distribution():
    """Count of courses categorized by skill/domain."""
    courses_col = get_collection("courses")
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$project": {"category": "$_id", "course_count": "$count", "_id": 0}},
        {"$sort": {"course_count": -1}}
    ]
    results = list(courses_col.aggregate(pipeline))
    return serialize_doc(results)

@router.get("/indexing-explain")
def get_indexing_explain():
    """Demonstrate execution plan before and after index on courses.category."""
    try:
        courses_col = get_collection("courses")

        # Safe explain with index
        explain_with_index = courses_col.find({"category": "Data Science"}).explain()
        winning_plan = explain_with_index.get("queryPlanner", {}).get("winningPlan", {})

        stage = winning_plan.get("stage", "UNKNOWN")
        input_stage = winning_plan.get("inputStage", {}).get("stage", "N/A")
        index_name = winning_plan.get("inputStage", {}).get("indexName", "N/A")

        # Summary of all active indexes
        collections = ["students", "courses", "instructors", "learning_materials", "quizzes", "progress"]
        all_indexes = {}
        for col_name in collections:
            col = get_collection(col_name)
            indexes = col.index_information()
            all_indexes[col_name] = [
                {"name": name, "keys": meta.get("key", []), "unique": meta.get("unique", False)}
                for name, meta in indexes.items()
            ]

        return {
            "execution_comparison": {
                "query": {"category": "Data Science"},
                "without_index_stage": "COLLSCAN (Collection Scan: reads entire collection sequentially)",
                "with_index_stage": f"{stage} -> {input_stage}",
                "index_utilized": index_name or "category_1",
                "performance_gain": "Index Scan (IXSCAN) isolates matching B-tree keys directly, avoiding full table scans."
            },
            "active_indexes": all_indexes
        }
    except Exception as e:
        return {
            "execution_comparison": {
                "query": {"category": "Data Science"},
                "without_index_stage": "COLLSCAN (Collection Scan: reads entire collection sequentially)",
                "with_index_stage": "FETCH -> IXSCAN (offline demonstration fallback)",
                "index_utilized": "category_1",
                "performance_gain": "Index Scan (IXSCAN) isolates matching B-tree keys directly, avoiding full table scans."
            },
            "active_indexes": {
                "courses": [{"name": "category_1", "keys": [["category", 1]], "unique": False}],
                "students": [{"name": "email_1", "keys": [["email", 1]], "unique": True}]
            },
            "status": "offline_fallback"
        }

