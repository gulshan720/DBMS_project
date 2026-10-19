"""
Offline Unit & Validation Test Suite
Runs completely in offline mode (no running MongoDB or Neo4j daemon required).
Validates Pydantic schemas, data serializations, exception handling,
FastAPI app routes, and graceful offline fallback responses.
"""

import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from bson import ObjectId

# Set up paths
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Pydantic schemas
from app.routers.students import StudentCreate, StudentUpdate, EnrollRequest
from app.routers.courses import CourseCreate, CourseUpdate
from app.routers.materials import MaterialCreate, MaterialUpdate
from app.routers.quizzes import QuizCreate, QuestionItem, ProgressUpdate, QuizScoreSubmit
from app.services.mongo_service import serialize_doc
from app.main import app
from app.routers.health import check_health
from app.routers.dashboard import get_dashboard_stats
from app.routers.analytics import get_indexing_explain
from app.routers.graph import get_graph_summary
from pydantic import ValidationError


class TestPydanticValidation(unittest.TestCase):
    """Test data validation and constraints on Pydantic schemas."""

    def test_student_create_valid(self):
        s = StudentCreate(
            student_id="S099",
            name="Alice Smith",
            email="alice.smith@university.edu",
            phone="+1234567890",
            enrollment_date="2026-01-15T00:00:00",
            courses_enrolled=["C001", "C002"]
        )
        self.assertEqual(s.student_id, "S099")
        self.assertEqual(len(s.courses_enrolled), 2)

    def test_student_create_invalid_id(self):
        with self.assertRaises(ValidationError):
            StudentCreate(
                student_id="STUDENT123",  # Must match ^S[0-9]{3,}$
                name="Alice Smith",
                email="alice@test.com",
                phone="+1234567890"
            )

    def test_student_create_invalid_email(self):
        with self.assertRaises(ValidationError):
            StudentCreate(
                student_id="S100",
                name="Alice Smith",
                email="not-an-email",
                phone="+1234567890"
            )

    def test_course_create_valid(self):
        c = CourseCreate(
            course_id="C099",
            title="Distributed Systems Engineering",
            category="Database Systems",
            difficulty_level="Advanced",
            instructor_id="I001",
            duration_hours=40,
            price=1999.0
        )
        self.assertEqual(c.difficulty_level, "Advanced")
        self.assertEqual(c.price, 1999.0)

    def test_course_create_invalid_difficulty(self):
        with self.assertRaises(ValidationError):
            CourseCreate(
                course_id="C099",
                title="Invalid Course",
                category="AI",
                difficulty_level="Master",  # Allowed: Beginner, Intermediate, Advanced
                instructor_id="I001",
                duration_hours=10,
                price=50.0
            )

    def test_material_create_valid(self):
        m = MaterialCreate(
            material_id="M099",
            course_id="C001",
            title="Introduction to B-Trees Slides",
            type="pdf",
            content_url="https://portal.edu/materials/m099.pdf",
            duration_minutes=30,
            order_index=1
        )
        self.assertEqual(m.type, "pdf")

    def test_material_create_invalid_type(self):
        with self.assertRaises(ValidationError):
            MaterialCreate(
                material_id="M099",
                course_id="C001",
                title="Unknown Material",
                type="audiobook",  # Allowed: video, pdf, article
                content_url="https://portal.edu/audio.mp3"
            )

    def test_quiz_create_valid(self):
        q = QuizCreate(
            quiz_id="Q099",
            course_id="C001",
            title="Midterm Assessment",
            total_points=50,
            time_limit_minutes=30,
            questions=[
                QuestionItem(
                    question_id="Q099_1",
                    question_text="What does ACID stand for?",
                    options=["Atomicity, Consistency, Isolation, Durability", "Action, Code, Index, Data"],
                    correct_answer="Atomicity, Consistency, Isolation, Durability",
                    points=25
                )
            ]
        )
        self.assertEqual(len(q.questions), 1)
        self.assertEqual(q.total_points, 50)

    def test_progress_update_bounds(self):
        # Valid bounds: 0 to 100
        p = ProgressUpdate(completion_percentage=75.5)
        self.assertEqual(p.completion_percentage, 75.5)

        with self.assertRaises(ValidationError):
            ProgressUpdate(completion_percentage=-5.0)

        with self.assertRaises(ValidationError):
            ProgressUpdate(completion_percentage=105.0)


class TestMongoSerialization(unittest.TestCase):
    """Test BSON to JSON serializable conversion."""

    def test_serialize_object_id_and_datetime(self):
        oid = ObjectId("64f8a1b2c3d4e5f6a7b8c9d0")
        dt = datetime(2026, 3, 15, 10, 30, 0)
        doc = {
            "_id": oid,
            "title": "Test Title",
            "created_at": dt,
            "tags": ["nosql", "graph"],
            "nested": {
                "sub_id": oid,
                "score": 95.5
            }
        }
        res = serialize_doc(doc)
        # Note: serialize_doc maps _id to id for client convenience
        self.assertEqual(res["id"], str(oid))
        self.assertEqual(res["created_at"], dt.isoformat())
        self.assertEqual(res["nested"]["sub_id"], str(oid))
        self.assertEqual(res["nested"]["score"], 95.5)

    def test_serialize_list(self):
        oid1 = ObjectId("64f8a1b2c3d4e5f6a7b8c9d0")
        oid2 = ObjectId("64f8a1b2c3d4e5f6a7b8c9d1")
        docs = [{"_id": oid1}, {"_id": oid2}]
        res = serialize_doc(docs)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["id"], str(oid1))
        self.assertEqual(res[1]["id"], str(oid2))


class TestFastAPIRoutesAndOfflineDegradation(unittest.TestCase):
    """Test API routes presence and offline resilience directly."""

    def test_openapi_schema_generated(self):
        schema = app.openapi()
        self.assertIn("Online Learning Portal", schema["info"]["title"])
        
        # Check required tags are registered
        paths = schema["paths"]
        self.assertIn("/api/health", paths)
        self.assertIn("/api/dashboard/stats", paths)
        self.assertIn("/api/students", paths)
        self.assertIn("/api/courses", paths)
        self.assertIn("/api/materials", paths)
        self.assertIn("/api/quizzes", paths)
        self.assertIn("/api/analytics/course-completion", paths)
        self.assertIn("/api/graph/summary", paths)

    def test_health_endpoint_offline_resilience(self):
        import json
        resp = check_health()
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.body.decode("utf-8"))
        self.assertIn(data["status"], ["healthy", "degraded"])
        self.assertIn("databases", data)
        self.assertIn("mongodb", data["databases"])
        self.assertIn("neo4j", data["databases"])

    def test_dashboard_stats_offline_resilience(self):
        data = get_dashboard_stats()
        self.assertIn("mongodb", data)
        self.assertIn("neo4j", data)
        self.assertIn("counts", data["mongodb"])

    def test_analytics_indexing_explain_offline_resilience(self):
        data = get_indexing_explain()
        self.assertIn("execution_comparison", data)
        self.assertIn("with_index_stage", data["execution_comparison"])

    def test_graph_summary_offline_resilience(self):
        data = get_graph_summary()
        self.assertIn("metrics", data)
        self.assertIn("total_nodes", data["metrics"])

    def test_app_routes_registered(self):
        route_paths = [getattr(r, "path", "") for r in app.routes]
        self.assertIn("/", route_paths)
        self.assertIn("/static", route_paths)
        schema = app.openapi()
        self.assertIn("/api/health", schema["paths"])
        self.assertIn("/api/students", schema["paths"])
        self.assertIn("/api/courses", schema["paths"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
