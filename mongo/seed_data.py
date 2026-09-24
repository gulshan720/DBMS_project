import os
import sys
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import get_mongo_db, close_connections

def drop_all():
    """Drops all collections to start fresh."""
    db = get_mongo_db()
    collections = ["students", "courses", "instructors", "learning_materials", "quizzes", "progress"]
    for coll in collections:
        db[coll].drop()
        print(f"Dropped collection '{coll}'.")

def seed_all():
    """Seeds database with sample data."""
    db = get_mongo_db()
    now = datetime.now()

    print("Seeding instructors...")
    instructors = [
        {"instructor_id": "I001", "name": "Rahul Sharma", "email": "rahul.s@example.com", "specialization": "Data Science", "bio": "Data Scientist with 10 years experience", "rating": 4.8, "courses_taught": ["C001", "C002"]},
        {"instructor_id": "I002", "name": "Priya Patel", "email": "priya.p@example.com", "specialization": "Web Development", "bio": "Full stack developer", "rating": 4.9, "courses_taught": ["C003", "C004"]},
        {"instructor_id": "I003", "name": "Amit Kumar", "email": "amit.k@example.com", "specialization": "Cloud Computing", "bio": "AWS Certified Architect", "rating": 4.7, "courses_taught": ["C005", "C006"]},
        {"instructor_id": "I004", "name": "Neha Gupta", "email": "neha.g@example.com", "specialization": "Cyber Security", "bio": "Security Consultant", "rating": 4.5, "courses_taught": ["C007", "C008"]},
        {"instructor_id": "I005", "name": "Vikram Singh", "email": "vikram.s@example.com", "specialization": "Mobile Dev", "bio": "Android & iOS expert", "rating": 4.6, "courses_taught": ["C009", "C010"]}
    ]
    db.instructors.insert_many(instructors)

    print("Seeding courses...")
    courses = [
        {"course_id": "C001", "title": "Data Science Fundamentals", "description": "Intro to Data Science", "category": "Data Science", "difficulty_level": "Beginner", "instructor_id": "I001", "duration_hours": 40, "price": 199.99, "created_date": now - timedelta(days=100)},
        {"course_id": "C002", "title": "Advanced Machine Learning", "description": "Deep Learning and AI", "category": "Data Science", "difficulty_level": "Advanced", "instructor_id": "I001", "duration_hours": 60, "price": 299.99, "created_date": now - timedelta(days=90)},
        {"course_id": "C003", "title": "JavaScript for Beginners", "description": "Learn JS from scratch", "category": "Web Dev", "difficulty_level": "Beginner", "instructor_id": "I002", "duration_hours": 30, "price": 99.99, "created_date": now - timedelta(days=80)},
        {"course_id": "C004", "title": "React Masterclass", "description": "Advanced React concepts", "category": "Web Dev", "difficulty_level": "Intermediate", "instructor_id": "I002", "duration_hours": 45, "price": 149.99, "created_date": now - timedelta(days=70)},
        {"course_id": "C005", "title": "AWS Solutions Architect", "description": "Pass the AWS cert", "category": "Cloud Computing", "difficulty_level": "Intermediate", "instructor_id": "I003", "duration_hours": 50, "price": 249.99, "created_date": now - timedelta(days=60)},
        {"course_id": "C006", "title": "Azure Fundamentals", "description": "AZ-900 Prep", "category": "Cloud Computing", "difficulty_level": "Beginner", "instructor_id": "I003", "duration_hours": 20, "price": 89.99, "created_date": now - timedelta(days=50)},
        {"course_id": "C007", "title": "Ethical Hacking 101", "description": "Learn ethical hacking", "category": "Cyber Security", "difficulty_level": "Beginner", "instructor_id": "I004", "duration_hours": 35, "price": 129.99, "created_date": now - timedelta(days=40)},
        {"course_id": "C008", "title": "Network Security", "description": "Secure your networks", "category": "Cyber Security", "difficulty_level": "Intermediate", "instructor_id": "I004", "duration_hours": 40, "price": 159.99, "created_date": now - timedelta(days=30)},
        {"course_id": "C009", "title": "Android App Dev", "description": "Build Android apps with Kotlin", "category": "Mobile App Dev", "difficulty_level": "Intermediate", "instructor_id": "I005", "duration_hours": 55, "price": 179.99, "created_date": now - timedelta(days=20)},
        {"course_id": "C010", "title": "iOS Dev with Swift", "description": "Build iPhone apps", "category": "Mobile App Dev", "difficulty_level": "Intermediate", "instructor_id": "I005", "duration_hours": 50, "price": 189.99, "created_date": now - timedelta(days=10)},
    ]
    db.courses.insert_many(courses)

    print("Seeding students...")
    students = [
        {"student_id": "S001", "name": "Aarav Joshi", "email": "aarav.j@example.com", "phone": "9876543210", "enrollment_date": now - timedelta(days=50), "courses_enrolled": ["C001", "C003"]},
        {"student_id": "S002", "name": "Vihaan Reddy", "email": "vihaan.r@example.com", "phone": "9876543211", "enrollment_date": now - timedelta(days=45), "courses_enrolled": ["C002"]},
        {"student_id": "S003", "name": "Ananya Desai", "email": "ananya.d@example.com", "phone": "9876543212", "enrollment_date": now - timedelta(days=40), "courses_enrolled": ["C003", "C004", "C005"]},
        {"student_id": "S004", "name": "Diya Iyer", "email": "diya.i@example.com", "phone": "9876543213", "enrollment_date": now - timedelta(days=35), "courses_enrolled": ["C007"]},
        {"student_id": "S005", "name": "Aditya Verma", "email": "aditya.v@example.com", "phone": "9876543214", "enrollment_date": now - timedelta(days=30), "courses_enrolled": ["C001", "C005"]},
        {"student_id": "S006", "name": "Kavya Menon", "email": "kavya.m@example.com", "phone": "9876543215", "enrollment_date": now - timedelta(days=25), "courses_enrolled": ["C009", "C010"]},
        {"student_id": "S007", "name": "Aryan Nair", "email": "aryan.n@example.com", "phone": "9876543216", "enrollment_date": now - timedelta(days=20), "courses_enrolled": ["C006", "C008"]},
        {"student_id": "S008", "name": "Ishaan Patil", "email": "ishaan.p@example.com", "phone": "9876543217", "enrollment_date": now - timedelta(days=15), "courses_enrolled": ["C001"]},
        {"student_id": "S009", "name": "Myra Kapoor", "email": "myra.k@example.com", "phone": "9876543218", "enrollment_date": now - timedelta(days=10), "courses_enrolled": ["C004"]},
        {"student_id": "S010", "name": "Riya Singh", "email": "riya.s@example.com", "phone": "9876543219", "enrollment_date": now - timedelta(days=5), "courses_enrolled": ["C002", "C003"]}
    ]
    db.students.insert_many(students)

    print("Seeding learning materials...")
    materials = []
    mat_id = 1
    for c in courses:
        # Add 1-2 materials per course
        for i in range(random.randint(1, 2)):
            materials.append({
                "material_id": f"M{mat_id:03d}",
                "course_id": c["course_id"],
                "title": f"Lecture {i+1} for {c['title']}",
                "type": random.choice(["video", "pdf", "article"]),
                "content_url": f"http://example.com/mat/{mat_id}",
                "duration_minutes": random.randint(10, 60),
                "order_index": i
            })
            mat_id += 1
    # Ensure at least 15
    while len(materials) < 15:
        materials.append({
            "material_id": f"M{mat_id:03d}",
            "course_id": "C001",
            "title": f"Extra Material {mat_id}",
            "type": "video",
            "content_url": f"http://example.com/mat/{mat_id}",
            "duration_minutes": 20,
            "order_index": 5
        })
        mat_id += 1
    db.learning_materials.insert_many(materials)

    print("Seeding quizzes...")
    quizzes = [
        {"quiz_id": "Q001", "course_id": "C001", "title": "Data Science Basics Quiz", "total_points": 10, "time_limit_minutes": 15, "questions": [
            {"question_id": "Q001_1", "question_text": "What is Python?", "options": ["Snake", "Language", "OS", "Car"], "correct_answer": "Language", "points": 5},
            {"question_id": "Q001_2", "question_text": "What is Pandas?", "options": ["Animal", "Library", "Food", "Book"], "correct_answer": "Library", "points": 5}
        ]},
        {"quiz_id": "Q002", "course_id": "C003", "title": "JS Basics", "total_points": 20, "time_limit_minutes": 20, "questions": [
            {"question_id": "Q002_1", "question_text": "Is JS typed?", "options": ["Yes", "No"], "correct_answer": "No", "points": 10},
            {"question_id": "Q002_2", "question_text": "What does DOM stand for?", "options": ["Document Object Model", "Disk", "Data"], "correct_answer": "Document Object Model", "points": 10}
        ]},
        {"quiz_id": "Q003", "course_id": "C005", "title": "AWS Quiz", "total_points": 15, "time_limit_minutes": 10, "questions": [
            {"question_id": "Q003_1", "question_text": "What is EC2?", "options": ["Compute", "Storage", "Database"], "correct_answer": "Compute", "points": 15}
        ]},
        {"quiz_id": "Q004", "course_id": "C007", "title": "Security Quiz", "total_points": 10, "time_limit_minutes": 15, "questions": [
            {"question_id": "Q004_1", "question_text": "What is Phishing?", "options": ["Fishing", "Social Engineering", "Hardware"], "correct_answer": "Social Engineering", "points": 10}
        ]},
        {"quiz_id": "Q005", "course_id": "C009", "title": "Android Quiz", "total_points": 10, "time_limit_minutes": 5, "questions": [
            {"question_id": "Q005_1", "question_text": "What is an Activity?", "options": ["Screen", "Service", "Broadcast"], "correct_answer": "Screen", "points": 10}
        ]}
    ]
    db.quizzes.insert_many(quizzes)

    print("Seeding progress records...")
    progress = [
        {"progress_id": "P001", "student_id": "S001", "course_id": "C001", "completion_percentage": 100, "last_accessed": now - timedelta(days=2), "status": "completed", "quiz_scores": [{"quiz_id": "Q001", "score": 10, "max_score": 10, "attempt_date": now - timedelta(days=2)}]},
        {"progress_id": "P002", "student_id": "S001", "course_id": "C003", "completion_percentage": 50, "last_accessed": now - timedelta(days=1), "status": "in_progress", "quiz_scores": []},
        {"progress_id": "P003", "student_id": "S002", "course_id": "C002", "completion_percentage": 10, "last_accessed": now, "status": "in_progress", "quiz_scores": []},
        {"progress_id": "P004", "student_id": "S003", "course_id": "C003", "completion_percentage": 100, "last_accessed": now - timedelta(days=10), "status": "completed", "quiz_scores": [{"quiz_id": "Q002", "score": 20, "max_score": 20, "attempt_date": now - timedelta(days=10)}]},
        {"progress_id": "P005", "student_id": "S003", "course_id": "C004", "completion_percentage": 80, "last_accessed": now - timedelta(days=3), "status": "in_progress", "quiz_scores": []},
        {"progress_id": "P006", "student_id": "S003", "course_id": "C005", "completion_percentage": 20, "last_accessed": now - timedelta(days=2), "status": "in_progress", "quiz_scores": []},
        {"progress_id": "P007", "student_id": "S004", "course_id": "C007", "completion_percentage": 100, "last_accessed": now - timedelta(days=1), "status": "completed", "quiz_scores": [{"quiz_id": "Q004", "score": 8, "max_score": 10, "attempt_date": now - timedelta(days=1)}]},
        {"progress_id": "P008", "student_id": "S005", "course_id": "C001", "completion_percentage": 90, "last_accessed": now - timedelta(days=1), "status": "in_progress", "quiz_scores": [{"quiz_id": "Q001", "score": 8, "max_score": 10, "attempt_date": now - timedelta(days=2)}]},
        {"progress_id": "P009", "student_id": "S005", "course_id": "C005", "completion_percentage": 100, "last_accessed": now - timedelta(days=5), "status": "completed", "quiz_scores": [{"quiz_id": "Q003", "score": 15, "max_score": 15, "attempt_date": now - timedelta(days=5)}]},
        {"progress_id": "P010", "student_id": "S006", "course_id": "C009", "completion_percentage": 30, "last_accessed": now, "status": "in_progress", "quiz_scores": []}
    ]
    db.progress.insert_many(progress)

    print("Data seeding completed successfully!")

if __name__ == '__main__':
    try:
        drop_all()
        seed_all()
    finally:
        close_connections()
