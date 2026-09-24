import os
import sys
from tabulate import tabulate

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import get_mongo_db, close_connections

def average_completion_per_course():
    """1. Average completion percentage per course (with course title lookup)"""
    print("\n--- Average Completion Percentage Per Course ---")
    db = get_mongo_db()
    pipeline = [
        {"$group": {
            "_id": "$course_id",
            "avg_completion": {"$avg": "$completion_percentage"}
        }},
        {"$lookup": {
            "from": "courses",
            "localField": "_id",
            "foreignField": "course_id",
            "as": "course_info"
        }},
        {"$unwind": "$course_info"},
        {"$project": {
            "course_id": "$_id",
            "title": "$course_info.title",
            "average_completion": {"$round": ["$avg_completion", 2]},
            "_id": 0
        }},
        {"$sort": {"average_completion": -1}}
    ]
    results = list(db.progress.aggregate(pipeline))
    print(tabulate(results, headers="keys"))

def top_3_students_completed_courses():
    """2. Top 3 students by number of completed courses"""
    print("\n--- Top 3 Students by Number of Completed Courses ---")
    db = get_mongo_db()
    pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": "$student_id",
            "completed_count": {"$sum": 1}
        }},
        {"$sort": {"completed_count": -1}},
        {"$limit": 3},
        {"$lookup": {
            "from": "students",
            "localField": "_id",
            "foreignField": "student_id",
            "as": "student_info"
        }},
        {"$unwind": "$student_info"},
        {"$project": {
            "student_name": "$student_info.name",
            "completed_courses_count": "$completed_count",
            "_id": 0
        }}
    ]
    results = list(db.progress.aggregate(pipeline))
    print(tabulate(results, headers="keys"))

def course_revenue_analysis():
    """3. Course revenue analysis (count enrolled students * price)"""
    print("\n--- Course Revenue Analysis ---")
    db = get_mongo_db()
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
            "as": "course_info"
        }},
        {"$unwind": "$course_info"},
        {"$project": {
            "course_title": "$course_info.title",
            "enrolled_students": "$enrolled_count",
            "price": "$course_info.price",
            "estimated_revenue": {"$multiply": ["$enrolled_count", "$course_info.price"]},
            "_id": 0
        }},
        {"$sort": {"estimated_revenue": -1}}
    ]
    results = list(db.students.aggregate(pipeline))
    print(tabulate(results, headers="keys"))

def quiz_performance_analysis():
    """4. Quiz performance analysis (average scores per quiz)"""
    print("\n--- Quiz Performance Analysis ---")
    db = get_mongo_db()
    pipeline = [
        {"$unwind": "$quiz_scores"},
        {"$group": {
            "_id": "$quiz_scores.quiz_id",
            "average_score": {"$avg": "$quiz_scores.score"},
            "attempts_count": {"$sum": 1}
        }},
        {"$lookup": {
            "from": "quizzes",
            "localField": "_id",
            "foreignField": "quiz_id",
            "as": "quiz_info"
        }},
        {"$unwind": "$quiz_info"},
        {"$project": {
            "quiz_title": "$quiz_info.title",
            "course_id": "$quiz_info.course_id",
            "average_score": {"$round": ["$average_score", 2]},
            "attempts": "$attempts_count",
            "_id": 0
        }},
        {"$sort": {"average_score": -1}}
    ]
    results = list(db.progress.aggregate(pipeline))
    print(tabulate(results, headers="keys"))

def learning_materials_count_by_type():
    """5. Learning materials count by type across all courses"""
    print("\n--- Learning Materials Count by Type ---")
    db = get_mongo_db()
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
    results = list(db.learning_materials.aggregate(pipeline))
    print(tabulate(results, headers="keys"))

# Aliases for compatibility
avg_completion_per_course = average_completion_per_course
top_students_by_completions = top_3_students_completed_courses
materials_count_by_type = learning_materials_count_by_type


def main():
    """Run all aggregation pipelines."""
    try:
        average_completion_per_course()
        top_3_students_completed_courses()
        course_revenue_analysis()
        quiz_performance_analysis()
        learning_materials_count_by_type()
    except ImportError:
        print("Please install tabulate: pip install tabulate")


if __name__ == '__main__':
    try:
        main()
    finally:
        close_connections()
