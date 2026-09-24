"""
Neo4j Schema Setup for Online Learning Portal
===============================================
Creates uniqueness constraints and indexes for the graph database schema.

Node types: Student, Course, Instructor, Skill, Category
Constraints ensure data integrity; indexes improve query performance.
"""

import os
import sys

# Allow running this file directly from the neo4j_db directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import get_neo4j_driver, close_connections


# ---------------------------------------------------------------------------
# Constraint definitions
# ---------------------------------------------------------------------------

UNIQUENESS_CONSTRAINTS = [
    {
        "name": "unique_student_id",
        "query": "CREATE CONSTRAINT unique_student_id IF NOT EXISTS "
                 "FOR (s:Student) REQUIRE s.student_id IS UNIQUE",
        "description": "Student.student_id uniqueness",
    },
    {
        "name": "unique_course_id",
        "query": "CREATE CONSTRAINT unique_course_id IF NOT EXISTS "
                 "FOR (c:Course) REQUIRE c.course_id IS UNIQUE",
        "description": "Course.course_id uniqueness",
    },
    {
        "name": "unique_instructor_id",
        "query": "CREATE CONSTRAINT unique_instructor_id IF NOT EXISTS "
                 "FOR (i:Instructor) REQUIRE i.instructor_id IS UNIQUE",
        "description": "Instructor.instructor_id uniqueness",
    },
    {
        "name": "unique_skill_id",
        "query": "CREATE CONSTRAINT unique_skill_id IF NOT EXISTS "
                 "FOR (sk:Skill) REQUIRE sk.skill_id IS UNIQUE",
        "description": "Skill.skill_id uniqueness",
    },
    {
        "name": "unique_category_name",
        "query": "CREATE CONSTRAINT unique_category_name IF NOT EXISTS "
                 "FOR (cat:Category) REQUIRE cat.name IS UNIQUE",
        "description": "Category.name uniqueness",
    },
]

INDEX_DEFINITIONS = [
    {
        "name": "idx_course_category",
        "query": "CREATE INDEX idx_course_category IF NOT EXISTS "
                 "FOR (c:Course) ON (c.category)",
        "description": "Index on Course.category",
    },
    {
        "name": "idx_student_email",
        "query": "CREATE INDEX idx_student_email IF NOT EXISTS "
                 "FOR (s:Student) ON (s.email)",
        "description": "Index on Student.email",
    },
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_constraints(driver):
    """Create all uniqueness constraints in the Neo4j database.

    Parameters
    ----------
    driver : neo4j.Driver
        An active Neo4j driver instance.
    """
    print("\n" + "=" * 60)
    print("  Creating Uniqueness Constraints")
    print("=" * 60)

    with driver.session() as session:
        for constraint in UNIQUENESS_CONSTRAINTS:
            try:
                session.run(constraint["query"])
                print(f"  [OK]  {constraint['description']}")
            except Exception as exc:
                print(f"  [ERR] {constraint['description']}: {exc}")


def create_indexes(driver):
    """Create performance indexes in the Neo4j database.

    Parameters
    ----------
    driver : neo4j.Driver
        An active Neo4j driver instance.
    """
    print("\n" + "=" * 60)
    print("  Creating Indexes")
    print("=" * 60)

    with driver.session() as session:
        for index in INDEX_DEFINITIONS:
            try:
                session.run(index["query"])
                print(f"  [OK]  {index['description']}")
            except Exception as exc:
                print(f"  [ERR] {index['description']}: {exc}")


def drop_all_constraints_and_indexes(driver):
    """Drop every user-created constraint and index (useful for a clean reset).

    Parameters
    ----------
    driver : neo4j.Driver
        An active Neo4j driver instance.
    """
    print("\n" + "=" * 60)
    print("  Dropping Existing Constraints & Indexes")
    print("=" * 60)

    with driver.session() as session:
        # Drop constraints
        result = session.run("SHOW CONSTRAINTS")
        for record in result:
            name = record["name"]
            try:
                session.run(f"DROP CONSTRAINT {name} IF EXISTS")
                print(f"  [DROPPED] Constraint: {name}")
            except Exception as exc:
                print(f"  [SKIP]    Constraint {name}: {exc}")

        # Drop indexes (skip lookup indexes which cannot be dropped)
        result = session.run("SHOW INDEXES")
        for record in result:
            name = record["name"]
            idx_type = record.get("type", "")
            if idx_type in ("LOOKUP",):
                continue
            try:
                session.run(f"DROP INDEX {name} IF EXISTS")
                print(f"  [DROPPED] Index: {name}")
            except Exception as exc:
                print(f"  [SKIP]    Index {name}: {exc}")


def show_schema(driver):
    """Print current constraints and indexes for verification.

    Parameters
    ----------
    driver : neo4j.Driver
        An active Neo4j driver instance.
    """
    print("\n" + "=" * 60)
    print("  Current Schema Summary")
    print("=" * 60)

    with driver.session() as session:
        print("\n  Constraints:")
        result = session.run("SHOW CONSTRAINTS")
        records = list(result)
        if not records:
            print("    (none)")
        for rec in records:
            print(f"    - {rec['name']}  ({rec.get('type', 'N/A')})")

        print("\n  Indexes:")
        result = session.run("SHOW INDEXES")
        records = list(result)
        if not records:
            print("    (none)")
        for rec in records:
            print(f"    - {rec['name']}  ({rec.get('type', 'N/A')})")


def setup_schema(driver=None):
    """One-call convenience: create all constraints and indexes, then verify."""
    should_close = False
    if driver is None:
        driver = get_neo4j_driver()
        should_close = True
    try:
        create_constraints(driver)
        create_indexes(driver)
        show_schema(driver)
        print("\n✅ Schema setup complete.\n")
    finally:
        if should_close:
            close_connections()


def main(driver=None):
    """Entry point for demo CLI and direct execution."""
    setup_schema(driver)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
