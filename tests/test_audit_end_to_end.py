"""
End-to-End Automated Audit & Test Suite
Tests API endpoints, CRUD operations, database synchronization,
graceful error handling, and verifies baseline data preservation.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# Setup path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.db_config import get_mongo_db, get_neo4j_driver

BASE_URL = "http://127.0.0.1:8000"

def http_request(path, method="GET", data=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"} if data else {}
    req_body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=req_body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"error": body}
        return e.code, parsed
    except Exception as e:
        return 500, {"error": str(e)}

def restore_clean_baseline():
    """Ensure no test leftover artifacts exist before/after tests."""
    db = get_mongo_db()
    # Remove any test IDs
    db.students.delete_many({"student_id": {"$regex": "^S99"}})
    db.courses.delete_many({"course_id": {"$regex": "^C99"}})
    db.learning_materials.delete_many({"material_id": {"$regex": "^M99"}})
    db.quizzes.delete_many({"quiz_id": {"$regex": "^Q99"}})
    db.progress.delete_many({"$or": [
        {"student_id": {"$regex": "^S99"}},
        {"course_id": {"$regex": "^C99"}},
        {"progress_id": "P_S001_C005"}
    ]})
    db.students.update_one({"student_id": "S001"}, {"$pull": {"courses_enrolled": "C005"}})

    driver = get_neo4j_driver()
    with driver.session() as s:
        s.run("MATCH (st:Student) WHERE st.student_id STARTS WITH 'S99' DETACH DELETE st")
        s.run("MATCH (c:Course) WHERE c.course_id STARTS WITH 'C99' DETACH DELETE c")
        s.run("MATCH (cat:Category {name: 'Artificial Intelligence'}) DETACH DELETE cat")
        s.run("MATCH (st:Student {student_id: 'S001'})-[r:ENROLLED_IN]->(c:Course {course_id: 'C005'}) DELETE r")

def get_current_counts():
    db = get_mongo_db()
    mongo_counts = {
        col: db[col].count_documents({})
        for col in ["students", "courses", "instructors", "learning_materials", "quizzes", "progress"]
    }
    driver = get_neo4j_driver()
    with driver.session() as s:
        nodes = s.run("MATCH (n) RETURN count(n) AS cnt").single()["cnt"]
        rels = s.run("MATCH ()-[r]->() RETURN count(r) AS cnt").single()["cnt"]
    return mongo_counts, nodes, rels

def run_tests():
    print("=" * 60)
    print("Online Learning Portal - Comprehensive Audit & Verification")
    print("=" * 60)

    # 1. Clean and check baseline
    restore_clean_baseline()
    m_counts, nodes, rels = get_current_counts()
    total_m = sum(m_counts.values())
    print(f"\n[Baseline Verification]")
    print(f"MongoDB documents: {total_m} {m_counts}")
    print(f"Neo4j nodes: {nodes}, relationships: {rels}")
    assert total_m == 57, f"Expected 57 MongoDB documents, got {total_m}"
    assert nodes == 52, f"Expected 52 Neo4j nodes, got {nodes}"
    assert rels == 72, f"Expected 72 Neo4j relationships, got {rels}"
    print("PASS: Baseline data verified (57 Mongo docs, 52 Neo4j nodes, 72 rels)")

    # 2. Health & System Status
    print("\n[Health & System Telemetry]")
    status, res = http_request("/api/health")
    assert status == 200 and res.get("status") == "healthy", f"Health check failed: {res}"
    print("PASS: /api/health -> healthy")

    status, res = http_request("/api/dashboard/stats")
    assert status == 200, f"Dashboard stats failed: {res}"
    assert res["mongodb"]["counts"]["students"] == 10
    assert res["mongodb"]["counts"]["courses"] == 10
    print("PASS: /api/dashboard/stats -> live telemetry verified")

    # 3. Read Endpoints
    print("\n[Read Operations]")
    for path, name in [
        ("/api/students", "Students"),
        ("/api/courses", "Courses"),
        ("/api/materials", "Materials"),
        ("/api/quizzes", "Quizzes"),
        ("/api/courses/meta", "Courses Meta"),
        ("/api/quizzes/progress/all", "All Progress")
    ]:
        status, data = http_request(path)
        assert status == 200, f"GET {path} failed with {status}"
        assert len(data) > 0, f"GET {path} returned empty result"
        print(f"PASS: GET {path} ({name}): returned {len(data)} records")

    # 4. MongoDB Aggregations & Indexing
    print("\n[MongoDB Aggregations & Index Explain]")
    for path, name in [
        ("/api/analytics/course-completion", "Course Completion"),
        ("/api/analytics/top-students", "Top Students"),
        ("/api/analytics/revenue", "Course Revenue"),
        ("/api/analytics/quiz-performance", "Quiz Performance"),
        ("/api/analytics/materials-distribution", "Materials Distribution"),
        ("/api/analytics/skill-distribution", "Skill Distribution"),
        ("/api/analytics/indexing-explain", "Indexing Explain")
    ]:
        status, data = http_request(path)
        assert status == 200, f"{path} failed: {status}"
        print(f"PASS: {path} ({name}) verified")

    # 5. Neo4j Graph Traversals & Cypher Analytics
    print("\n[Neo4j Graph Traversals & Analytics]")
    for path, name in [
        ("/api/graph/summary", "Graph Summary"),
        ("/api/graph/prerequisites/C004", "Prerequisites (C004)"),
        ("/api/graph/learning-path?start_course_id=C001&end_course_id=C004", "Learning Path (C001 -> C004)"),
        ("/api/graph/recommendations/S001", "Recommendations (S001)"),
        ("/api/graph/peer-cohort/S001", "Peer Cohort (S001)"),
        ("/api/graph/analytics/popularity", "Course Popularity"),
        ("/api/graph/analytics/instructor-workload", "Instructor Workload"),
        ("/api/graph/analytics/category-statistics", "Category Statistics"),
        ("/api/graph/analytics/prerequisite-depth", "Prerequisite Depth"),
        ("/api/graph/analytics/skill-gap/S001", "Skill Gap (S001)"),
        ("/api/graph/network-graph?limit=25", "Network Graph D3")
    ]:
        status, data = http_request(path)
        assert status == 200, f"{path} failed: {status}"
        print(f"PASS: {path} ({name}) verified")

    # 6. Graceful Handling of Unknown IDs
    print("\n[Graceful Error Handling for Unknown IDs]")
    status, data = http_request("/api/graph/prerequisites/UNKNOWN_C999")
    assert status == 200 and data.get("prerequisites") == [], "Unknown course prereqs failed"
    print("PASS: Unknown course prerequisites handled gracefully (empty list returned)")

    status, data = http_request("/api/graph/recommendations/UNKNOWN_S999")
    assert status == 200 and data.get("recommendations") == [], "Unknown student recs failed"
    print("PASS: Unknown student recommendations handled gracefully (empty list returned)")

    status, data = http_request("/api/graph/instructor-network/UNKNOWN_I999")
    assert status == 404, f"Expected 404 for unknown instructor network, got {status}"
    print("PASS: Unknown instructor network returns clean 404")

    # 7. Student Full CRUD & Enrollment Cycle
    print("\n[Student CRUD & Enrollment Cycle]")
    test_sid = "S991"
    # CREATE
    status, res = http_request("/api/students", method="POST", data={
        "student_id": test_sid,
        "name": "Audit Test Student",
        "email": "audit.test@portal.edu",
        "phone": "9998887770"
    })
    assert status == 201, f"Student create failed: {status} {res}"
    print(f"PASS: POST /api/students -> Created {test_sid}")

    # DUPLICATE REJECTION
    status, res = http_request("/api/students", method="POST", data={
        "student_id": test_sid,
        "name": "Duplicate Student",
        "email": "duplicate@portal.edu",
        "phone": "9998887771"
    })
    assert status == 409, f"Duplicate student ID was not rejected: {status}"
    print(f"PASS: Duplicate student ID {test_sid} rejected with 409 Conflict")

    # READ
    status, res = http_request(f"/api/students/{test_sid}")
    assert status == 200 and res["student"]["name"] == "Audit Test Student"
    print(f"PASS: GET /api/students/{test_sid} -> Verified details")

    # UPDATE
    status, res = http_request(f"/api/students/{test_sid}", method="PUT", data={
        "name": "Audit Test Student Updated"
    })
    assert status == 200
    status, res = http_request(f"/api/students/{test_sid}")
    assert res["student"]["name"] == "Audit Test Student Updated"
    print(f"PASS: PUT /api/students/{test_sid} -> Updated name verified")

    # ENROLL
    status, res = http_request(f"/api/students/{test_sid}/enroll", method="POST", data={"course_id": "C001"})
    assert status == 200, f"Enroll failed: {res}"
    # Verify Neo4j enrollment sync
    driver = get_neo4j_driver()
    with driver.session() as s:
        rec = s.run("MATCH (st:Student {student_id: $sid})-[:ENROLLED_IN]->(c:Course {course_id: 'C001'}) RETURN count(c) AS cnt", sid=test_sid).single()["cnt"]
        assert rec == 1, "Neo4j enrollment relationship not created"
    print(f"PASS: POST /api/students/{test_sid}/enroll -> Verified in MongoDB and Neo4j")

    # DELETE
    status, res = http_request(f"/api/students/{test_sid}", method="DELETE")
    assert status == 200
    status, res = http_request(f"/api/students/{test_sid}")
    assert status == 404
    # Verify Neo4j deletion
    with driver.session() as s:
        rec = s.run("MATCH (st:Student {student_id: $sid}) RETURN count(st) AS cnt", sid=test_sid).single()["cnt"]
        assert rec == 0, "Neo4j student node not deleted"
    print(f"PASS: DELETE /api/students/{test_sid} -> Removed from MongoDB and Neo4j")

    # 8. Course Full CRUD Cycle
    print("\n[Course CRUD Cycle]")
    test_cid = "C991"
    # CREATE
    status, res = http_request("/api/courses", method="POST", data={
        "course_id": test_cid,
        "title": "Autonomous Agent Systems",
        "category": "Data Science",
        "difficulty_level": "Advanced",
        "instructor_id": "I001",
        "duration_hours": 36,
        "price": 3499.0
    })
    assert status == 201, f"Course create failed: {status} {res}"
    print(f"PASS: POST /api/courses -> Created {test_cid}")

    # READ
    status, res = http_request(f"/api/courses/{test_cid}")
    assert status == 200 and res["course"]["title"] == "Autonomous Agent Systems"
    print(f"PASS: GET /api/courses/{test_cid} -> Verified course details")

    # UPDATE
    status, res = http_request(f"/api/courses/{test_cid}", method="PUT", data={"price": 3999.0})
    assert status == 200
    status, res = http_request(f"/api/courses/{test_cid}")
    assert res["course"]["price"] == 3999.0
    print(f"PASS: PUT /api/courses/{test_cid} -> Updated price verified")

    # DELETE
    status, res = http_request(f"/api/courses/{test_cid}", method="DELETE")
    assert status == 200
    status, res = http_request(f"/api/courses/{test_cid}")
    assert status == 404
    with driver.session() as s:
        rec = s.run("MATCH (c:Course {course_id: $cid}) RETURN count(c) AS cnt", cid=test_cid).single()["cnt"]
        assert rec == 0, "Neo4j course node not deleted"
    print(f"PASS: DELETE /api/courses/{test_cid} -> Removed from MongoDB and Neo4j")

    # 9. Learning Material Full CRUD Cycle
    print("\n[Learning Material CRUD Cycle]")
    test_mid = "M991"
    # CREATE
    status, res = http_request("/api/materials", method="POST", data={
        "material_id": test_mid,
        "course_id": "C001",
        "title": "Interactive PyMongo Guide",
        "type": "article",
        "content_url": "https://example.com/materials/pymongo-guide",
        "duration_minutes": 25,
        "order_index": 99
    })
    assert status == 201, f"Material create failed: {status} {res}"
    print(f"PASS: POST /api/materials -> Created {test_mid}")

    # READ
    status, res = http_request(f"/api/materials/{test_mid}")
    assert status == 200 and res["title"] == "Interactive PyMongo Guide"
    print(f"PASS: GET /api/materials/{test_mid} -> Verified material details")

    # UPDATE
    status, res = http_request(f"/api/materials/{test_mid}", method="PUT", data={"duration_minutes": 30})
    assert status == 200
    status, res = http_request(f"/api/materials/{test_mid}")
    assert res["duration_minutes"] == 30
    print(f"PASS: PUT /api/materials/{test_mid} -> Updated duration verified")

    # DELETE
    status, res = http_request(f"/api/materials/{test_mid}", method="DELETE")
    assert status == 200
    status, res = http_request(f"/api/materials/{test_mid}")
    assert status == 404
    print(f"PASS: DELETE /api/materials/{test_mid} -> Removed material")

    # 10. Quiz Full CRUD Cycle
    print("\n[Quiz CRUD Cycle]")
    test_qid = "Q991"
    # CREATE
    status, res = http_request("/api/quizzes", method="POST", data={
        "quiz_id": test_qid,
        "course_id": "C001",
        "title": "NoSQL Architecture Quiz",
        "total_points": 25,
        "time_limit_minutes": 20,
        "questions": [
            {
                "question_id": f"{test_qid}_1",
                "question_text": "What type of database is MongoDB?",
                "options": ["Document", "Graph", "Relational", "Key-Value"],
                "correct_answer": "Document",
                "points": 25
            }
        ]
    })
    assert status == 201, f"Quiz create failed: {status} {res}"
    print(f"PASS: POST /api/quizzes -> Created {test_qid}")

    # READ
    status, res = http_request(f"/api/quizzes/{test_qid}")
    assert status == 200 and res["title"] == "NoSQL Architecture Quiz"
    print(f"PASS: GET /api/quizzes/{test_qid} -> Verified quiz details")

    # UPDATE
    status, res = http_request(f"/api/quizzes/{test_qid}", method="PUT", data={"total_points": 30})
    assert status == 200
    status, res = http_request(f"/api/quizzes/{test_qid}")
    assert res["total_points"] == 30
    print(f"PASS: PUT /api/quizzes/{test_qid} -> Updated total points verified")

    # DELETE
    status, res = http_request(f"/api/quizzes/{test_qid}", method="DELETE")
    assert status == 200
    status, res = http_request(f"/api/quizzes/{test_qid}")
    assert status == 404
    print(f"PASS: DELETE /api/quizzes/{test_qid} -> Removed quiz")

    # 11. Final Baseline Verification
    print("\n[Post-Audit Baseline Integrity Check]")
    restore_clean_baseline()
    m_final, nodes_final, rels_final = get_current_counts()
    total_m_final = sum(m_final.values())
    print(f"MongoDB documents: {total_m_final} {m_final}")
    print(f"Neo4j nodes: {nodes_final}, relationships: {rels_final}")
    assert total_m_final == 57, f"Data integrity violation: MongoDB docs {total_m_final} != 57"
    assert nodes_final == 52, f"Data integrity violation: Neo4j nodes {nodes_final} != 52"
    assert rels_final == 72, f"Data integrity violation: Neo4j rels {rels_final} != 72"
    print("PASS: 100% Data Integrity Preserved! Exactly 57 Mongo docs & 52 Neo4j nodes / 72 rels.")

    print("\n" + "=" * 60)
    print("ALL AUDIT AND INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
