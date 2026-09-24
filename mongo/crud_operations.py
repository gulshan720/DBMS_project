import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import get_mongo_db, close_connections

# CRUD functions

def create_student(data):
    """Creates a new student."""
    print(f"Creating student: {data.get('name')}")
    db = get_mongo_db()
    result = db.students.insert_one(data)
    print(f"Inserted student with _id: {result.inserted_id}")
    return result

def create_course(data):
    """Creates a new course."""
    print(f"Creating course: {data.get('title')}")
    db = get_mongo_db()
    result = db.courses.insert_one(data)
    print(f"Inserted course with _id: {result.inserted_id}")
    return result

def create_instructor(data):
    """Creates a new instructor."""
    print(f"Creating instructor: {data.get('name')}")
    db = get_mongo_db()
    result = db.instructors.insert_one(data)
    print(f"Inserted instructor with _id: {result.inserted_id}")
    return result

def get_student(student_id):
    """Fetches a student by ID."""
    print(f"Fetching student: {student_id}")
    db = get_mongo_db()
    return db.students.find_one({"student_id": student_id})

def get_course(course_id):
    """Fetches a course by ID."""
    print(f"Fetching course: {course_id}")
    db = get_mongo_db()
    return db.courses.find_one({"course_id": course_id})

def get_all_courses():
    """Fetches all courses."""
    print("Fetching all courses")
    db = get_mongo_db()
    return list(db.courses.find({}))

def get_courses_by_category(category):
    """Fetches courses by category."""
    print(f"Fetching courses for category: {category}")
    db = get_mongo_db()
    return list(db.courses.find({"category": category}))

def update_student_email(student_id, new_email):
    """Updates a student's email."""
    print(f"Updating email for student: {student_id} to {new_email}")
    db = get_mongo_db()
    result = db.students.update_one({"student_id": student_id}, {"$set": {"email": new_email}})
    print(f"Modified count: {result.modified_count}")

def update_progress(student_id, course_id, percentage):
    """Updates completion percentage in progress record."""
    print(f"Updating progress for student {student_id}, course {course_id} to {percentage}%")
    db = get_mongo_db()
    
    status = "completed" if percentage == 100 else "in_progress"
    
    result = db.progress.update_one(
        {"student_id": student_id, "course_id": course_id},
        {"$set": {"completion_percentage": percentage, "status": status, "last_accessed": datetime.now()}}
    )
    print(f"Modified count: {result.modified_count}")

def delete_student(student_id):
    """Deletes a student."""
    print(f"Deleting student: {student_id}")
    db = get_mongo_db()
    result = db.students.delete_one({"student_id": student_id})
    print(f"Deleted count: {result.deleted_count}")

def delete_quiz(quiz_id):
    """Deletes a quiz."""
    print(f"Deleting quiz: {quiz_id}")
    db = get_mongo_db()
    result = db.quizzes.delete_one({"quiz_id": quiz_id})
    print(f"Deleted count: {result.deleted_count}")

def enroll_student(student_id, course_id):
    """Enrolls a student in a course by updating the student document and creating a progress record."""
    print(f"Enrolling student {student_id} in course {course_id}")
    db = get_mongo_db()
    
    # Update student
    db.students.update_one(
        {"student_id": student_id},
        {"$addToSet": {"courses_enrolled": course_id}}
    )
    
    # Create progress record if not exists
    progress_exists = db.progress.find_one({"student_id": student_id, "course_id": course_id})
    if not progress_exists:
        progress_data = {
            "progress_id": f"P_{student_id}_{course_id}",
            "student_id": student_id,
            "course_id": course_id,
            "completion_percentage": 0,
            "last_accessed": datetime.now(),
            "status": "enrolled",
            "quiz_scores": []
        }
        db.progress.insert_one(progress_data)
        print("Progress record created.")
    else:
        print("Progress record already exists.")

if __name__ == '__main__':
    try:
        # Create
        create_student({
            "student_id": "S999",
            "name": "Test Student",
            "email": "test@example.com",
            "enrollment_date": datetime.now(),
            "courses_enrolled": []
        })
        
        # Read
        student = get_student("S999")
        print(f"Found student: {student}")
        
        category_courses = get_courses_by_category("Data Science")
        print(f"Found {len(category_courses)} Data Science courses.")
        
        # Update
        update_student_email("S999", "test999@example.com")
        
        # Enroll & Progress
        enroll_student("S999", "C001")
        update_progress("S999", "C001", 50)
        
        # Delete
        delete_student("S999")
        print("Demo completed.")
    finally:
        close_connections()
