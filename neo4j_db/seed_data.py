"""
Neo4j Seed Data for Online Learning Portal
============================================
Populates the graph database with sample nodes and relationships.

Nodes (40 total):
    - 10 Students  (S001–S010, realistic Indian names)
    - 10 Courses   (C001–C010, matching MongoDB titles)
    -  5 Instructors (I001–I005)
    - 10 Skills
    -  5 Categories

Relationships (63+ total):
    - 15  ENROLLED_IN
    -  5  COMPLETED
    - 10  HAS_SKILL  (students)
    -  5  TEACHES
    -  5  PREREQUISITE_OF
    - 10  BELONGS_TO
    -  8  REQUIRES_SKILL
    -  5  HAS_SKILL  (instructors)

All writes use MERGE so the script is idempotent.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import get_neo4j_driver, close_connections


# ──────────────────────────────────────────────────────────────────────────────
# Node data
# ──────────────────────────────────────────────────────────────────────────────

STUDENTS = [
    {"student_id": "S001", "name": "Aarav Sharma",    "email": "aarav.sharma@email.com",    "enrollment_date": "2025-01-15"},
    {"student_id": "S002", "name": "Priya Patel",     "email": "priya.patel@email.com",     "enrollment_date": "2025-02-01"},
    {"student_id": "S003", "name": "Rohan Mehta",     "email": "rohan.mehta@email.com",     "enrollment_date": "2025-02-20"},
    {"student_id": "S004", "name": "Ananya Gupta",    "email": "ananya.gupta@email.com",    "enrollment_date": "2025-03-10"},
    {"student_id": "S005", "name": "Vikram Singh",    "email": "vikram.singh@email.com",    "enrollment_date": "2025-03-25"},
    {"student_id": "S006", "name": "Sneha Reddy",     "email": "sneha.reddy@email.com",     "enrollment_date": "2025-04-05"},
    {"student_id": "S007", "name": "Arjun Nair",      "email": "arjun.nair@email.com",      "enrollment_date": "2025-04-18"},
    {"student_id": "S008", "name": "Kavya Iyer",      "email": "kavya.iyer@email.com",      "enrollment_date": "2025-05-02"},
    {"student_id": "S009", "name": "Rahul Deshmukh",  "email": "rahul.deshmukh@email.com",  "enrollment_date": "2025-05-15"},
    {"student_id": "S010", "name": "Meera Joshi",     "email": "meera.joshi@email.com",     "enrollment_date": "2025-06-01"},
]

COURSES = [
    {"course_id": "C001", "title": "Python Programming Fundamentals",   "category": "Programming",      "difficulty_level": "Beginner",     "duration_hours": 40,  "price": 2999},
    {"course_id": "C002", "title": "Advanced Python & OOP",             "category": "Programming",      "difficulty_level": "Intermediate", "duration_hours": 50,  "price": 3999},
    {"course_id": "C003", "title": "Data Science with Python",          "category": "Data Science",     "difficulty_level": "Intermediate", "duration_hours": 60,  "price": 4999},
    {"course_id": "C004", "title": "Machine Learning A-Z",              "category": "Data Science",     "difficulty_level": "Advanced",     "duration_hours": 80,  "price": 5999},
    {"course_id": "C005", "title": "Web Development with Django",       "category": "Web Development",  "difficulty_level": "Intermediate", "duration_hours": 55,  "price": 4499},
    {"course_id": "C006", "title": "JavaScript Essentials",             "category": "Programming",      "difficulty_level": "Beginner",     "duration_hours": 35,  "price": 2499},
    {"course_id": "C007", "title": "React & Frontend Development",      "category": "Web Development",  "difficulty_level": "Intermediate", "duration_hours": 45,  "price": 3999},
    {"course_id": "C008", "title": "Cloud Computing with AWS",          "category": "Cloud & DevOps",   "difficulty_level": "Advanced",     "duration_hours": 70,  "price": 6999},
    {"course_id": "C009", "title": "DevOps & CI/CD Pipelines",          "category": "Cloud & DevOps",   "difficulty_level": "Advanced",     "duration_hours": 65,  "price": 5999},
    {"course_id": "C010", "title": "Cybersecurity Fundamentals",        "category": "Security",         "difficulty_level": "Beginner",     "duration_hours": 40,  "price": 3499},
]

INSTRUCTORS = [
    {"instructor_id": "I001", "name": "Dr. Rajesh Kumar",    "specialization": "Python & Data Science",  "rating": 4.8},
    {"instructor_id": "I002", "name": "Prof. Sunita Verma",  "specialization": "Web Development",        "rating": 4.6},
    {"instructor_id": "I003", "name": "Dr. Amit Jain",       "specialization": "Machine Learning & AI",  "rating": 4.9},
    {"instructor_id": "I004", "name": "Prof. Neha Kapoor",   "specialization": "Cloud & DevOps",         "rating": 4.7},
    {"instructor_id": "I005", "name": "Dr. Suresh Babu",     "specialization": "Cybersecurity",          "rating": 4.5},
]

SKILLS = [
    {"skill_id": "SK001", "name": "Python",             "description": "General-purpose programming language"},
    {"skill_id": "SK002", "name": "JavaScript",         "description": "Client-side and server-side scripting language"},
    {"skill_id": "SK003", "name": "SQL",                "description": "Structured Query Language for databases"},
    {"skill_id": "SK004", "name": "Machine Learning",   "description": "Algorithms that learn from data"},
    {"skill_id": "SK005", "name": "Data Analysis",      "description": "Inspecting and modeling data"},
    {"skill_id": "SK006", "name": "Cloud Computing",    "description": "On-demand delivery of IT resources via the cloud"},
    {"skill_id": "SK007", "name": "Cybersecurity",      "description": "Protection of systems, networks, and data"},
    {"skill_id": "SK008", "name": "Web Development",    "description": "Building and maintaining websites"},
    {"skill_id": "SK009", "name": "DevOps",             "description": "Practices combining development and operations"},
    {"skill_id": "SK010", "name": "Mobile Development", "description": "Creating applications for mobile devices"},
]

CATEGORIES = [
    {"name": "Programming",      "description": "General programming and software development courses"},
    {"name": "Data Science",     "description": "Data analysis, machine learning, and AI courses"},
    {"name": "Web Development",  "description": "Frontend and backend web development courses"},
    {"name": "Cloud & DevOps",   "description": "Cloud platforms, containerization, and CI/CD courses"},
    {"name": "Security",         "description": "Cybersecurity and information security courses"},
]


# ──────────────────────────────────────────────────────────────────────────────
# Relationship data
# ──────────────────────────────────────────────────────────────────────────────

# 15 ENROLLED_IN relationships
ENROLLED_IN = [
    {"student_id": "S001", "course_id": "C001", "enrollment_date": "2025-01-20", "status": "active"},
    {"student_id": "S001", "course_id": "C003", "enrollment_date": "2025-02-10", "status": "active"},
    {"student_id": "S002", "course_id": "C001", "enrollment_date": "2025-02-05", "status": "active"},
    {"student_id": "S002", "course_id": "C005", "enrollment_date": "2025-03-01", "status": "active"},
    {"student_id": "S003", "course_id": "C002", "enrollment_date": "2025-03-01", "status": "active"},
    {"student_id": "S003", "course_id": "C004", "enrollment_date": "2025-03-15", "status": "active"},
    {"student_id": "S004", "course_id": "C006", "enrollment_date": "2025-03-12", "status": "active"},
    {"student_id": "S004", "course_id": "C007", "enrollment_date": "2025-04-01", "status": "active"},
    {"student_id": "S005", "course_id": "C008", "enrollment_date": "2025-04-01", "status": "active"},
    {"student_id": "S005", "course_id": "C009", "enrollment_date": "2025-04-15", "status": "active"},
    {"student_id": "S006", "course_id": "C001", "enrollment_date": "2025-04-10", "status": "active"},
    {"student_id": "S006", "course_id": "C010", "enrollment_date": "2025-04-20", "status": "active"},
    {"student_id": "S007", "course_id": "C003", "enrollment_date": "2025-05-01", "status": "active"},
    {"student_id": "S008", "course_id": "C005", "enrollment_date": "2025-05-10", "status": "active"},
    {"student_id": "S009", "course_id": "C002", "enrollment_date": "2025-05-20", "status": "active"},
]

# 5 COMPLETED relationships
COMPLETED = [
    {"student_id": "S001", "course_id": "C001", "completion_date": "2025-03-15", "grade": "A"},
    {"student_id": "S002", "course_id": "C001", "completion_date": "2025-04-10", "grade": "A+"},
    {"student_id": "S003", "course_id": "C002", "completion_date": "2025-05-20", "grade": "B+"},
    {"student_id": "S006", "course_id": "C001", "completion_date": "2025-06-15", "grade": "A"},
    {"student_id": "S009", "course_id": "C002", "completion_date": "2025-07-25", "grade": "B"},
]

# 10 HAS_SKILL for students
STUDENT_SKILLS = [
    {"student_id": "S001", "skill_id": "SK001", "proficiency_level": "Intermediate"},
    {"student_id": "S001", "skill_id": "SK003", "proficiency_level": "Beginner"},
    {"student_id": "S002", "skill_id": "SK001", "proficiency_level": "Advanced"},
    {"student_id": "S003", "skill_id": "SK001", "proficiency_level": "Intermediate"},
    {"student_id": "S003", "skill_id": "SK004", "proficiency_level": "Beginner"},
    {"student_id": "S004", "skill_id": "SK002", "proficiency_level": "Intermediate"},
    {"student_id": "S005", "skill_id": "SK006", "proficiency_level": "Beginner"},
    {"student_id": "S006", "skill_id": "SK001", "proficiency_level": "Beginner"},
    {"student_id": "S007", "skill_id": "SK005", "proficiency_level": "Intermediate"},
    {"student_id": "S008", "skill_id": "SK008", "proficiency_level": "Intermediate"},
]

# 5 TEACHES (each instructor teaches 1–2 courses)
TEACHES = [
    {"instructor_id": "I001", "course_id": "C001", "since": "2024-01-01"},
    {"instructor_id": "I001", "course_id": "C002", "since": "2024-06-01"},
    {"instructor_id": "I002", "course_id": "C005", "since": "2024-03-01"},
    {"instructor_id": "I003", "course_id": "C003", "since": "2024-02-01"},
    {"instructor_id": "I003", "course_id": "C004", "since": "2024-07-01"},
    {"instructor_id": "I004", "course_id": "C008", "since": "2024-04-01"},
    {"instructor_id": "I004", "course_id": "C009", "since": "2024-08-01"},
    {"instructor_id": "I005", "course_id": "C010", "since": "2024-05-01"},
    {"instructor_id": "I002", "course_id": "C006", "since": "2024-09-01"},
    {"instructor_id": "I002", "course_id": "C007", "since": "2024-10-01"},
]

# 5 PREREQUISITE_OF (prerequisite chains)
PREREQUISITES = [
    {"prerequisite_id": "C001", "course_id": "C002"},   # Python Fundamentals -> Advanced Python
    {"prerequisite_id": "C002", "course_id": "C003"},   # Advanced Python -> Data Science
    {"prerequisite_id": "C003", "course_id": "C004"},   # Data Science -> Machine Learning
    {"prerequisite_id": "C006", "course_id": "C007"},   # JS Essentials -> React
    {"prerequisite_id": "C001", "course_id": "C005"},   # Python Fundamentals -> Django
]

# 10 BELONGS_TO (every course belongs to a category)
BELONGS_TO = [
    {"course_id": "C001", "category_name": "Programming"},
    {"course_id": "C002", "category_name": "Programming"},
    {"course_id": "C003", "category_name": "Data Science"},
    {"course_id": "C004", "category_name": "Data Science"},
    {"course_id": "C005", "category_name": "Web Development"},
    {"course_id": "C006", "category_name": "Programming"},
    {"course_id": "C007", "category_name": "Web Development"},
    {"course_id": "C008", "category_name": "Cloud & DevOps"},
    {"course_id": "C009", "category_name": "Cloud & DevOps"},
    {"course_id": "C010", "category_name": "Security"},
]

# 8 REQUIRES_SKILL
REQUIRES_SKILL = [
    {"course_id": "C002", "skill_id": "SK001"},   # Advanced Python requires Python
    {"course_id": "C003", "skill_id": "SK001"},   # Data Science requires Python
    {"course_id": "C003", "skill_id": "SK005"},   # Data Science requires Data Analysis
    {"course_id": "C004", "skill_id": "SK004"},   # ML requires Machine Learning basics
    {"course_id": "C005", "skill_id": "SK001"},   # Django requires Python
    {"course_id": "C007", "skill_id": "SK002"},   # React requires JavaScript
    {"course_id": "C008", "skill_id": "SK006"},   # AWS requires Cloud Computing
    {"course_id": "C009", "skill_id": "SK009"},   # DevOps requires DevOps basics
]

# 5 HAS_SKILL for instructors
INSTRUCTOR_SKILLS = [
    {"instructor_id": "I001", "skill_id": "SK001", "proficiency_level": "Expert"},
    {"instructor_id": "I002", "skill_id": "SK008", "proficiency_level": "Expert"},
    {"instructor_id": "I003", "skill_id": "SK004", "proficiency_level": "Expert"},
    {"instructor_id": "I004", "skill_id": "SK006", "proficiency_level": "Expert"},
    {"instructor_id": "I005", "skill_id": "SK007", "proficiency_level": "Expert"},
]


# ──────────────────────────────────────────────────────────────────────────────
# Helper: run a Cypher statement inside a transaction
# ──────────────────────────────────────────────────────────────────────────────

def _run(session, query, **kwargs):
    """Execute a single Cypher statement with keyword parameters."""
    session.run(query, **kwargs)


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def clear_all(driver=None):
    """Delete every node and relationship in the database.

    Parameters
    ----------
    driver : neo4j.Driver, optional
        An active Neo4j driver instance. If None, one will be created.
    """
    if driver is None:
        driver = get_neo4j_driver()
    print("\n🗑️  Clearing all nodes and relationships …")
    with driver.session() as session:
        result = session.run("MATCH (n) DETACH DELETE n")
        summary = result.consume()
        print(f"   Deleted {summary.counters.nodes_deleted} nodes, "
              f"{summary.counters.relationships_deleted} relationships.")


def seed_all(driver=None):
    """Populate the database with sample nodes and relationships.

    Uses MERGE so calling this multiple times is safe (idempotent).

    Parameters
    ----------
    driver : neo4j.Driver, optional
        An active Neo4j driver instance. If None, one will be created.
    """
    if driver is None:
        driver = get_neo4j_driver()
    with driver.session() as session:
        # ── Nodes ────────────────────────────────────────────────────────
        print("\n📦 Seeding Nodes …")

        # Students
        for s in STUDENTS:
            session.run(
                "MERGE (st:Student {student_id: $student_id}) "
                "SET st.name = $name, st.email = $email, "
                "    st.enrollment_date = $enrollment_date",
                student_id=s["student_id"], name=s["name"],
                email=s["email"], enrollment_date=s["enrollment_date"],
            )
        print(f"   ✔ Students:    {len(STUDENTS)}")

        # Courses
        for c in COURSES:
            session.run(
                "MERGE (cr:Course {course_id: $course_id}) "
                "SET cr.title = $title, cr.category = $category, "
                "    cr.difficulty_level = $difficulty_level, "
                "    cr.duration_hours = $duration_hours, cr.price = $price",
                course_id=c["course_id"], title=c["title"],
                category=c["category"], difficulty_level=c["difficulty_level"],
                duration_hours=c["duration_hours"], price=c["price"],
            )
        print(f"   ✔ Courses:     {len(COURSES)}")

        # Instructors
        for i in INSTRUCTORS:
            session.run(
                "MERGE (ins:Instructor {instructor_id: $instructor_id}) "
                "SET ins.name = $name, ins.specialization = $specialization, "
                "    ins.rating = $rating",
                instructor_id=i["instructor_id"], name=i["name"],
                specialization=i["specialization"], rating=i["rating"],
            )
        print(f"   ✔ Instructors: {len(INSTRUCTORS)}")

        # Skills
        for sk in SKILLS:
            session.run(
                "MERGE (s:Skill {skill_id: $skill_id}) "
                "SET s.name = $name, s.description = $description",
                skill_id=sk["skill_id"], name=sk["name"],
                description=sk["description"],
            )
        print(f"   ✔ Skills:      {len(SKILLS)}")

        # Categories
        for cat in CATEGORIES:
            session.run(
                "MERGE (c:Category {name: $name}) "
                "SET c.description = $description",
                name=cat["name"], description=cat["description"],
            )
        print(f"   ✔ Categories:  {len(CATEGORIES)}")

        total_nodes = (len(STUDENTS) + len(COURSES) + len(INSTRUCTORS)
                       + len(SKILLS) + len(CATEGORIES))
        print(f"   ── Total nodes: {total_nodes}")

        # ── Relationships ────────────────────────────────────────────────
        print("\n🔗 Seeding Relationships …")

        # ENROLLED_IN
        for e in ENROLLED_IN:
            session.run(
                "MATCH (s:Student {student_id: $student_id}), "
                "      (c:Course  {course_id:  $course_id}) "
                "MERGE (s)-[r:ENROLLED_IN]->(c) "
                "SET r.enrollment_date = $enrollment_date, r.status = $status",
                student_id=e["student_id"], course_id=e["course_id"],
                enrollment_date=e["enrollment_date"], status=e["status"],
            )
        print(f"   ✔ ENROLLED_IN:      {len(ENROLLED_IN)}")

        # COMPLETED
        for comp in COMPLETED:
            session.run(
                "MATCH (s:Student {student_id: $student_id}), "
                "      (c:Course  {course_id:  $course_id}) "
                "MERGE (s)-[r:COMPLETED]->(c) "
                "SET r.completion_date = $completion_date, r.grade = $grade",
                student_id=comp["student_id"], course_id=comp["course_id"],
                completion_date=comp["completion_date"], grade=comp["grade"],
            )
        print(f"   ✔ COMPLETED:        {len(COMPLETED)}")

        # HAS_SKILL (students)
        for ss in STUDENT_SKILLS:
            session.run(
                "MATCH (s:Student {student_id: $student_id}), "
                "      (sk:Skill  {skill_id:   $skill_id}) "
                "MERGE (s)-[r:HAS_SKILL]->(sk) "
                "SET r.proficiency_level = $proficiency_level",
                student_id=ss["student_id"], skill_id=ss["skill_id"],
                proficiency_level=ss["proficiency_level"],
            )
        print(f"   ✔ HAS_SKILL (stud): {len(STUDENT_SKILLS)}")

        # TEACHES
        for t in TEACHES:
            session.run(
                "MATCH (i:Instructor {instructor_id: $instructor_id}), "
                "      (c:Course     {course_id:     $course_id}) "
                "MERGE (i)-[r:TEACHES]->(c) "
                "SET r.since = $since",
                instructor_id=t["instructor_id"], course_id=t["course_id"],
                since=t["since"],
            )
        print(f"   ✔ TEACHES:          {len(TEACHES)}")

        # PREREQUISITE_OF
        for p in PREREQUISITES:
            session.run(
                "MATCH (pre:Course {course_id: $prerequisite_id}), "
                "      (crs:Course {course_id: $course_id}) "
                "MERGE (pre)-[:PREREQUISITE_OF]->(crs)",
                prerequisite_id=p["prerequisite_id"], course_id=p["course_id"],
            )
        print(f"   ✔ PREREQUISITE_OF:  {len(PREREQUISITES)}")

        # BELONGS_TO
        for b in BELONGS_TO:
            session.run(
                "MATCH (c:Course   {course_id: $course_id}), "
                "      (cat:Category {name:    $category_name}) "
                "MERGE (c)-[:BELONGS_TO]->(cat)",
                course_id=b["course_id"], category_name=b["category_name"],
            )
        print(f"   ✔ BELONGS_TO:       {len(BELONGS_TO)}")

        # REQUIRES_SKILL
        for rs in REQUIRES_SKILL:
            session.run(
                "MATCH (c:Course {course_id: $course_id}), "
                "      (sk:Skill {skill_id:  $skill_id}) "
                "MERGE (c)-[:REQUIRES_SKILL]->(sk)",
                course_id=rs["course_id"], skill_id=rs["skill_id"],
            )
        print(f"   ✔ REQUIRES_SKILL:   {len(REQUIRES_SKILL)}")

        # HAS_SKILL (instructors)
        for isk in INSTRUCTOR_SKILLS:
            session.run(
                "MATCH (i:Instructor {instructor_id: $instructor_id}), "
                "      (sk:Skill     {skill_id:      $skill_id}) "
                "MERGE (i)-[r:HAS_SKILL]->(sk) "
                "SET r.proficiency_level = $proficiency_level",
                instructor_id=isk["instructor_id"], skill_id=isk["skill_id"],
                proficiency_level=isk["proficiency_level"],
            )
        print(f"   ✔ HAS_SKILL (inst): {len(INSTRUCTOR_SKILLS)}")

        total_rels = (len(ENROLLED_IN) + len(COMPLETED) + len(STUDENT_SKILLS)
                      + len(TEACHES) + len(PREREQUISITES) + len(BELONGS_TO)
                      + len(REQUIRES_SKILL) + len(INSTRUCTOR_SKILLS))
        print(f"   ── Total relationships: {total_rels}")


def print_counts(driver=None):
    """Query and print node / relationship counts for verification.

    Parameters
    ----------
    driver : neo4j.Driver, optional
        An active Neo4j driver instance. If None, one will be created.
    """
    if driver is None:
        driver = get_neo4j_driver()
    print("\n📊 Database Counts")
    print("=" * 40)
    with driver.session() as session:
        # Node counts by label
        for label in ["Student", "Course", "Instructor", "Skill", "Category"]:
            result = session.run(f"MATCH (n:{label}) RETURN count(n) AS cnt")
            count = result.single()["cnt"]
            print(f"   {label:<15} {count}")

        # Total nodes
        result = session.run("MATCH (n) RETURN count(n) AS cnt")
        print(f"   {'TOTAL NODES':<15} {result.single()['cnt']}")

        # Relationship counts by type
        print()
        for rel_type in ["ENROLLED_IN", "COMPLETED", "HAS_SKILL", "TEACHES",
                         "PREREQUISITE_OF", "BELONGS_TO", "REQUIRES_SKILL"]:
            result = session.run(
                f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS cnt"
            )
            count = result.single()["cnt"]
            print(f"   {rel_type:<20} {count}")

        result = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt")
        print(f"   {'TOTAL RELS':<20} {result.single()['cnt']}")


def main(driver=None):
    """Entry point for seeding database."""
    should_close = False
    if driver is None:
        driver = get_neo4j_driver()
        should_close = True
    try:
        clear_all(driver)
        seed_all(driver)
        print_counts(driver)
        print("\n✅ Seeding complete.\n")
    finally:
        if should_close:
            close_connections()


# ──────────────────────────────────────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
