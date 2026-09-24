import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import get_mongo_db, close_connections

def create_indexes():
    """Creates useful indexes for the collections."""
    db = get_mongo_db()
    print("Creating indexes...")

    # students.email (unique)
    db.students.create_index("email", unique=True)
    print("Created unique index on students.email")

    # courses.category
    db.courses.create_index("category")
    print("Created index on courses.category")

    # courses.instructor_id
    db.courses.create_index("instructor_id")
    print("Created index on courses.instructor_id")

    # progress: compound index on (student_id, course_id)
    db.progress.create_index([("student_id", 1), ("course_id", 1)])
    print("Created compound index on progress (student_id, course_id)")

    # quizzes.course_id
    db.quizzes.create_index("course_id")
    print("Created index on quizzes.course_id")

def explain_query_before_after():
    """Demonstrates explain() output for a sample query."""
    db = get_mongo_db()
    
    # Drop index if exists to show "before"
    try:
        db.courses.drop_index("category_1")
    except:
        pass
        
    print("\n--- Query EXPLAIN Output WITHOUT Index on category ---")
    explain_no_index = db.courses.find({"category": "Data Science"}).explain()
    print(f"Winning Plan Stage: {explain_no_index['queryPlanner']['winningPlan']['stage']}")
    
    # Create the index
    db.courses.create_index("category")
    
    print("\n--- Query EXPLAIN Output WITH Index on category ---")
    explain_with_index = db.courses.find({"category": "Data Science"}).explain()
    
    # Get the winning plan
    winning_plan = explain_with_index['queryPlanner']['winningPlan']
    print(f"Winning Plan Stage: {winning_plan['stage']}")
    
    if 'inputStage' in winning_plan:
        print(f"Input Stage: {winning_plan['inputStage']['stage']}")
        print(f"Index Used: {winning_plan['inputStage'].get('indexName', 'N/A')}")
        
if __name__ == '__main__':
    try:
        explain_query_before_after()
        create_indexes()
    finally:
        close_connections()
