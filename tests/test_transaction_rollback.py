"""
Transaction Rollback & ACID Verification Test
Deliberately induces a failure inside a MongoDB multi-document transaction
and verifies that all changes (updates & inserts) are completely rolled back.
"""

import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.db_config import get_mongo_client, get_mongo_db, get_neo4j_driver

def run_rollback_verification():
    print("=" * 65)
    print("MongoDB ACID Multi-Document Transaction & Rollback Test")
    print("=" * 65)

    client = get_mongo_client()
    db = get_mongo_db()

    # Pre-clean isolated test records
    test_sid = "S_TRX_TEST"
    db.students.delete_many({"student_id": test_sid})
    db.progress.delete_many({"student_id": test_sid})

    # Record initial counts
    init_student_count = db.students.count_documents({})
    init_progress_count = db.progress.count_documents({})
    print(f"\n[1] Initial State: {init_student_count} students, {init_progress_count} progress records")

    # Step 1: Create isolated student
    db.students.insert_one({
        "student_id": test_sid,
        "name": "Transaction Rollback Learner",
        "email": "rollback.test@portal.edu",
        "phone": "9998881111",
        "enrollment_date": datetime(2026, 1, 1),
        "courses_enrolled": []
    })
    print(f"[2] Created isolated test student: {test_sid}")

    # Step 2: Successful Transaction Test
    print("\n[3] Testing SUCCESSFUL transaction commit...")
    with client.start_session() as session:
        with session.start_transaction():
            # Update student
            db.students.update_one(
                {"student_id": test_sid},
                {"$addToSet": {"courses_enrolled": "C001"}},
                session=session
            )
            # Insert progress
            db.progress.insert_one({
                "progress_id": f"P_{test_sid}_C001",
                "student_id": test_sid,
                "course_id": "C001",
                "completion_percentage": 0,
                "last_accessed": datetime.now(),
                "status": "enrolled",
                "quiz_scores": []
            }, session=session)

    # Verify commit succeeded
    st = db.students.find_one({"student_id": test_sid})
    pr = db.progress.find_one({"progress_id": f"P_{test_sid}_C001"})
    assert "C001" in st["courses_enrolled"], "Commit verification failed: C001 not in courses_enrolled"
    assert pr is not None, "Commit verification failed: progress record not created"
    print("  PASS: Successful transaction committed cleanly (both student and progress persisted)")

    # Step 3: Deliberate Failure & Rollback Test
    print("\n[4] Testing DELIBERATE FAILURE & automatic rollback...")
    rollback_occurred = False
    try:
        with client.start_session() as session:
            with session.start_transaction():
                # Attempt to add C002 to courses_enrolled
                db.students.update_one(
                    {"student_id": test_sid},
                    {"$addToSet": {"courses_enrolled": "C002"}},
                    session=session
                )
                # Attempt to insert progress for C002
                db.progress.insert_one({
                    "progress_id": f"P_{test_sid}_C002",
                    "student_id": test_sid,
                    "course_id": "C002",
                    "completion_percentage": 0,
                    "last_accessed": datetime.now(),
                    "status": "enrolled",
                    "quiz_scores": []
                }, session=session)

                # DELIBERATE EXCEPTION: Simulate downstream system failure before commit
                raise RuntimeError("Simulated payment/system failure during enrollment!")

    except RuntimeError as ex:
        print(f"  Captured deliberate exception as expected: '{ex}'")
        rollback_occurred = True

    assert rollback_occurred, "Exception was not triggered!"

    # Verify Rollback: Neither the student update nor the progress insert should exist
    st_after = db.students.find_one({"student_id": test_sid})
    pr_after = db.progress.find_one({"progress_id": f"P_{test_sid}_C002"})

    print(f"  Enrolled courses after aborted transaction: {st_after.get('courses_enrolled')}")
    assert "C002" not in st_after.get("courses_enrolled", []), (
        "ROLLBACK VIOLATION: C002 was found in courses_enrolled despite transaction abort!"
    )
    assert pr_after is None, (
        "ROLLBACK VIOLATION: Progress record P_..._C002 exists despite transaction abort!"
    )
    print("  PASS: 100% Rollback Confirmed! C002 was not added to student, and progress record was discarded.")

    # Step 4: Cleanup isolated test records
    print("\n[5] Cleaning up isolated test artifacts...")
    db.students.delete_many({"student_id": test_sid})
    db.progress.delete_many({"student_id": test_sid})

    # Step 5: Verify baseline counts
    final_students = db.students.count_documents({})
    final_progress = db.progress.count_documents({})
    assert final_students == init_student_count, (
        f"Baseline student count corrupted: {final_students} != {init_student_count}"
    )
    assert final_progress == init_progress_count, (
        f"Baseline progress count corrupted: {final_progress} != {init_progress_count}"
    )

    # Check total MongoDB documents
    total_mongo = sum(
        db[c].count_documents({})
        for c in ["students", "courses", "instructors", "learning_materials", "quizzes", "progress"]
    )
    assert total_mongo == 57, f"Total MongoDB document count mismatch: {total_mongo} != 57"

    # Check Neo4j baseline
    driver = get_neo4j_driver()
    with driver.session() as s:
        nodes = s.run("MATCH (n) RETURN count(n) AS cnt").single()["cnt"]
        rels = s.run("MATCH ()-[r]->() RETURN count(r) AS cnt").single()["cnt"]

    assert nodes == 52, f"Neo4j node count mismatch: {nodes} != 52"
    assert rels == 72, f"Neo4j rel count mismatch: {rels} != 72"

    print(f"  PASS: Post-test baseline pristine -> 57 MongoDB docs, 52 Neo4j nodes, 72 rels.")
    print("\n" + "=" * 65)
    print("TRANSACTION COMMIT AND ROLLBACK VERIFIED WITH ZERO DATA LEAKS!")
    print("=" * 65)


if __name__ == "__main__":
    run_rollback_verification()
