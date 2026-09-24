import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import get_mongo_db, close_connections

def setup_schemas():
    """Sets up JSON schema validation for all MongoDB collections."""
    db = get_mongo_db()
    
    # 1. students
    student_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["student_id", "name", "email", "enrollment_date"],
            "properties": {
                "student_id": {"bsonType": "string", "description": "must be a string and is required"},
                "name": {"bsonType": "string", "description": "must be a string and is required"},
                "email": {"bsonType": "string", "pattern": "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$", "description": "must be a valid email string and is required"},
                "phone": {"bsonType": "string", "description": "must be a string if provided"},
                "enrollment_date": {"bsonType": "date", "description": "must be a date and is required"},
                "courses_enrolled": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"},
                    "description": "must be an array of course_id strings"
                }
            }
        }
    }

    # 2. courses
    course_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["course_id", "title", "category", "instructor_id", "price"],
            "properties": {
                "course_id": {"bsonType": "string"},
                "title": {"bsonType": "string"},
                "description": {"bsonType": "string"},
                "category": {"bsonType": "string"},
                "difficulty_level": {"enum": ["Beginner", "Intermediate", "Advanced"]},
                "instructor_id": {"bsonType": "string"},
                "duration_hours": {"bsonType": "number"},
                "price": {"bsonType": "number"},
                "created_date": {"bsonType": "date"}
            }
        }
    }

    # 3. instructors
    instructor_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["instructor_id", "name", "email", "specialization"],
            "properties": {
                "instructor_id": {"bsonType": "string"},
                "name": {"bsonType": "string"},
                "email": {"bsonType": "string", "pattern": "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$"},
                "specialization": {"bsonType": "string"},
                "bio": {"bsonType": "string"},
                "rating": {"bsonType": "number", "minimum": 0, "maximum": 5},
                "courses_taught": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"}
                }
            }
        }
    }

    # 4. learning_materials
    material_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["material_id", "course_id", "title", "type", "content_url"],
            "properties": {
                "material_id": {"bsonType": "string"},
                "course_id": {"bsonType": "string"},
                "title": {"bsonType": "string"},
                "type": {"enum": ["video", "pdf", "article", "quiz"]},
                "content_url": {"bsonType": "string"},
                "duration_minutes": {"bsonType": "number"},
                "order_index": {"bsonType": "int"}
            }
        }
    }

    # 5. quizzes
    quiz_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["quiz_id", "course_id", "title", "questions"],
            "properties": {
                "quiz_id": {"bsonType": "string"},
                "course_id": {"bsonType": "string"},
                "title": {"bsonType": "string"},
                "questions": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": ["question_id", "question_text", "options", "correct_answer", "points"],
                        "properties": {
                            "question_id": {"bsonType": "string"},
                            "question_text": {"bsonType": "string"},
                            "options": {"bsonType": "array", "items": {"bsonType": "string"}},
                            "correct_answer": {"bsonType": "string"},
                            "points": {"bsonType": "number"}
                        }
                    }
                },
                "total_points": {"bsonType": "number"},
                "time_limit_minutes": {"bsonType": "number"}
            }
        }
    }

    # 6. progress
    progress_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["progress_id", "student_id", "course_id", "status"],
            "properties": {
                "progress_id": {"bsonType": "string"},
                "student_id": {"bsonType": "string"},
                "course_id": {"bsonType": "string"},
                "completion_percentage": {"bsonType": "number", "minimum": 0, "maximum": 100},
                "last_accessed": {"bsonType": "date"},
                "quiz_scores": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": ["quiz_id", "score", "max_score"],
                        "properties": {
                            "quiz_id": {"bsonType": "string"},
                            "score": {"bsonType": "number"},
                            "max_score": {"bsonType": "number"},
                            "attempt_date": {"bsonType": "date"}
                        }
                    }
                },
                "status": {"enum": ["enrolled", "in_progress", "completed"]}
            }
        }
    }

    collections_validators = {
        "students": student_validator,
        "courses": course_validator,
        "instructors": instructor_validator,
        "learning_materials": material_validator,
        "quizzes": quiz_validator,
        "progress": progress_validator
    }

    for coll_name, validator in collections_validators.items():
        if coll_name in db.list_collection_names():
            print(f"Collection '{coll_name}' already exists. Applying schema validation modification...")
            db.command({"collMod": coll_name, "validator": validator, "validationLevel": "strict"})
        else:
            print(f"Creating collection '{coll_name}' with schema validation...")
            db.create_collection(coll_name, validator=validator)
    
    print("Schema setup completed.")

# Aliases for compatibility
setup_all_schemas = setup_schemas
main = setup_schemas

if __name__ == '__main__':
    try:
        setup_schemas()
    finally:
        close_connections()
