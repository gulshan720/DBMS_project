import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import get_mongo_db, get_mongo_client, close_connections

# Note: Transactions require a replica set in MongoDB. 
# To test locally with a single node, you must start mongod with --replSet rs0 
# and initialize it using rs.initiate() in mongosh.

def enroll_student_transaction(student_id, course_id):
    """
    Multi-document transaction:
    1. Creates a progress record
    2. Updates student's courses_enrolled array
    """
    client = get_mongo_client()
    db = get_mongo_db()
    
    print(f"\n--- Running Enrollment Transaction for {student_id} into {course_id} ---")
    
    try:
        with client.start_session() as session:
            with session.start_transaction():
                
                # 1. Update Student
                result_student = db.students.update_one(
                    {"student_id": student_id},
                    {"$addToSet": {"courses_enrolled": course_id}},
                    session=session
                )
                print(f"Student update matched: {result_student.matched_count}")
                
                if result_student.matched_count == 0:
                    raise Exception("Student not found!")

                # 2. Insert Progress
                progress_id = f"P_{student_id}_{course_id}_trx"
                
                db.progress.insert_one({
                    "progress_id": progress_id,
                    "student_id": student_id,
                    "course_id": course_id,
                    "completion_percentage": 0,
                    "last_accessed": datetime.now(),
                    "status": "enrolled",
                    "quiz_scores": []
                }, session=session)
                print(f"Progress record created: {progress_id}")
                
                print("Transaction committed successfully.")
                
    except Exception as e:
        print(f"Transaction aborted due to error: {e}")

def transfer_student_transaction(student_id, old_course_id, new_course_id):
    """
    Multi-document transaction:
    1. Removes old course from student
    2. Adds new course to student
    3. Deletes old progress
    4. Creates new progress
    """
    client = get_mongo_client()
    db = get_mongo_db()
    
    print(f"\n--- Running Transfer Transaction for {student_id}: {old_course_id} -> {new_course_id} ---")
    
    try:
        with client.start_session() as session:
            with session.start_transaction():
                
                # 1. Unenroll from old course
                db.students.update_one(
                    {"student_id": student_id},
                    {"$pull": {"courses_enrolled": old_course_id}},
                    session=session
                )
                
                # 2. Enroll in new course
                db.students.update_one(
                    {"student_id": student_id},
                    {"$addToSet": {"courses_enrolled": new_course_id}},
                    session=session
                )
                
                # 3. Remove old progress
                db.progress.delete_one(
                    {"student_id": student_id, "course_id": old_course_id},
                    session=session
                )
                
                # 4. Create new progress
                db.progress.insert_one({
                    "progress_id": f"P_{student_id}_{new_course_id}_trx",
                    "student_id": student_id,
                    "course_id": new_course_id,
                    "completion_percentage": 0,
                    "last_accessed": datetime.now(),
                    "status": "enrolled",
                    "quiz_scores": []
                }, session=session)
                
                print("Transfer transaction committed successfully.")
                
    except Exception as e:
        print(f"Transfer transaction aborted due to error: {e}")


def main():
    """Run transaction demonstrations."""
    # Note: These require MongoDB running as a replica set
    try:
        enroll_student_transaction("S001", "C005")
        transfer_student_transaction("S002", "C002", "C003")
    except Exception as e:
        print(f"Transaction demo failed: {e}\nDid you configure a MongoDB replica set?")


if __name__ == '__main__':
    try:
        main()
    finally:
        close_connections()
