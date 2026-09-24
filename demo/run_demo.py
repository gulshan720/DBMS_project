#!/usr/bin/env python3
"""
Online Learning Portal – Interactive Demo CLI
==============================================
Menu-driven CLI to demonstrate all MongoDB and Neo4j operations
for Review 2 of the DBMS NoSQL project.

Usage:
    python demo/run_demo.py
"""

import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config.db_config import close_connections


# ─── Helper Utilities ───────────────────────────────────────────────────────

def print_header(title):
    """Print a formatted section header."""
    width = 60
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_menu(title, options):
    """Print a numbered menu and return the user's choice."""
    print_header(title)
    for i, option in enumerate(options, 1):
        print(f"  [{i}] {option}")
    print(f"  [0] Back / Exit")
    print("-" * 40)
    while True:
        try:
            choice = int(input("  Enter your choice: "))
            if 0 <= choice <= len(options):
                return choice
        except (ValueError, EOFError):
            pass
        print("  Invalid choice. Try again.")


def pause():
    """Pause and wait for user to press Enter."""
    try:
        input("\n  Press Enter to continue...")
    except (EOFError, KeyboardInterrupt):
        pass


# ─── MongoDB Demos ──────────────────────────────────────────────────────────

def mongo_schema_demo():
    """Demonstrate MongoDB schema validation setup."""
    print_header("MongoDB: Schema Design & Validation")
    from mongo.schema_design import setup_schemas
    setup_schemas()
    pause()


def mongo_seed_demo():
    """Seed MongoDB with sample data."""
    print_header("MongoDB: Seeding Sample Data (55+ documents)")
    from mongo.seed_data import drop_all, seed_all
    drop_all()
    seed_all()
    pause()


def mongo_crud_demo():
    """Demonstrate MongoDB CRUD operations."""
    from mongo.crud_operations import (
        create_student, get_student, get_all_courses,
        get_courses_by_category, update_student_email,
        update_progress, delete_quiz, enroll_student,
    )

    options = [
        "Create a new student",
        "Get student by ID",
        "Get all courses",
        "Get courses by category",
        "Update student email",
        "Update student progress",
        "Delete a quiz",
        "Enroll student in course",
        "Run ALL CRUD demos",
    ]

    while True:
        choice = print_menu("MongoDB: CRUD Operations", options)
        if choice == 0:
            break
        elif choice == 1:
            create_student({
                "student_id": "S999",
                "name": "Demo Student",
                "email": "demo@example.com",
                "phone": "9999999999",
                "enrollment_date": "2026-01-01",
                "courses_enrolled": [],
            })
        elif choice == 2:
            sid = input("  Enter student ID (e.g., S001): ").strip() or "S001"
            get_student(sid)
        elif choice == 3:
            get_all_courses()
        elif choice == 4:
            cat = input("  Enter category (e.g., Data Science): ").strip() or "Data Science"
            get_courses_by_category(cat)
        elif choice == 5:
            sid = input("  Enter student ID (e.g., S001): ").strip() or "S001"
            email = input("  Enter new email: ").strip() or "updated@example.com"
            update_student_email(sid, email)
        elif choice == 6:
            sid = input("  Enter student ID (e.g., S001): ").strip() or "S001"
            cid = input("  Enter course ID (e.g., C001): ").strip() or "C001"
            pct = input("  Enter completion % (e.g., 75): ").strip() or "75"
            update_progress(sid, cid, float(pct))
        elif choice == 7:
            qid = input("  Enter quiz ID (e.g., Q001): ").strip() or "Q001"
            delete_quiz(qid)
        elif choice == 8:
            sid = input("  Enter student ID (e.g., S001): ").strip() or "S001"
            cid = input("  Enter course ID (e.g., C005): ").strip() or "C005"
            enroll_student(sid, cid)
        elif choice == 9:
            print("\n  --- Running all CRUD demos ---")
            create_student({
                "student_id": "S999",
                "name": "Demo Student",
                "email": "demo@example.com",
                "phone": "9999999999",
                "enrollment_date": "2026-01-01",
                "courses_enrolled": [],
            })
            get_student("S001")
            get_all_courses()
            get_courses_by_category("Data Science")
            update_student_email("S999", "new_demo@example.com")
            update_progress("S001", "C001", 85.0)
            enroll_student("S001", "C005")
        pause()


def mongo_aggregation_demo():
    """Demonstrate MongoDB aggregation pipelines."""
    from mongo.aggregation import (
        avg_completion_per_course,
        top_students_by_completions,
        course_revenue_analysis,
        quiz_performance_analysis,
        materials_count_by_type,
    )

    options = [
        "Average completion per course",
        "Top 3 students by completions",
        "Course revenue analysis",
        "Quiz performance analysis",
        "Learning materials by type",
        "Run ALL aggregations",
    ]

    while True:
        choice = print_menu("MongoDB: Aggregation Pipelines", options)
        if choice == 0:
            break
        elif choice == 1:
            avg_completion_per_course()
        elif choice == 2:
            top_students_by_completions()
        elif choice == 3:
            course_revenue_analysis()
        elif choice == 4:
            quiz_performance_analysis()
        elif choice == 5:
            materials_count_by_type()
        elif choice == 6:
            print("\n  --- Running all aggregation pipelines ---")
            avg_completion_per_course()
            top_students_by_completions()
            course_revenue_analysis()
            quiz_performance_analysis()
            materials_count_by_type()
        pause()


def mongo_indexing_demo():
    """Demonstrate MongoDB indexing."""
    print_header("MongoDB: Indexing & Performance")
    from mongo.indexing import main as indexing_main
    indexing_main()
    pause()


def mongo_transactions_demo():
    """Demonstrate MongoDB transactions."""
    print_header("MongoDB: Multi-document Transactions")
    from mongo.transactions import main as transactions_main
    transactions_main()
    pause()


def mongo_menu():
    """MongoDB operations submenu."""
    options = [
        "Schema Design (Create collections with validation)",
        "Seed Data (Insert 55+ sample documents)",
        "CRUD Operations",
        "Aggregation Pipelines",
        "Indexing & Performance",
        "Transactions",
        "Full MongoDB Demo (run everything in sequence)",
    ]

    while True:
        choice = print_menu("MongoDB Operations", options)
        if choice == 0:
            break
        elif choice == 1:
            mongo_schema_demo()
        elif choice == 2:
            mongo_seed_demo()
        elif choice == 3:
            mongo_crud_demo()
        elif choice == 4:
            mongo_aggregation_demo()
        elif choice == 5:
            mongo_indexing_demo()
        elif choice == 6:
            mongo_transactions_demo()
        elif choice == 7:
            print_header("FULL MongoDB DEMO")
            mongo_schema_demo()
            mongo_seed_demo()
            mongo_indexing_demo()
            # Run all aggregations
            from mongo.aggregation import (
                avg_completion_per_course, top_students_by_completions,
                course_revenue_analysis, quiz_performance_analysis,
                materials_count_by_type,
            )
            print_header("MongoDB: All Aggregation Pipelines")
            avg_completion_per_course()
            top_students_by_completions()
            course_revenue_analysis()
            quiz_performance_analysis()
            materials_count_by_type()
            pause()


# ─── Neo4j Demos ────────────────────────────────────────────────────────────

def neo4j_schema_demo():
    """Demonstrate Neo4j schema setup."""
    print_header("Neo4j: Schema Setup (Constraints & Indexes)")
    from neo4j_db.schema_setup import main as schema_main
    schema_main()
    pause()


def neo4j_seed_demo():
    """Seed Neo4j with sample data."""
    print_header("Neo4j: Seeding Sample Data (50+ nodes, 60+ relationships)")
    from neo4j_db.seed_data import clear_all, seed_all
    clear_all()
    seed_all()
    pause()


def neo4j_crud_demo():
    """Demonstrate Neo4j CRUD operations."""
    print_header("Neo4j: CRUD Operations")
    from neo4j_db.crud_operations import main as crud_main
    crud_main()
    pause()


def neo4j_traversal_demo():
    """Demonstrate Neo4j graph traversal."""
    print_header("Neo4j: Graph Traversal Queries")
    from neo4j_db.graph_traversal import main as traversal_main
    traversal_main()
    pause()


def neo4j_advanced_demo():
    """Demonstrate Neo4j advanced queries."""
    print_header("Neo4j: Advanced Cypher Queries")
    from neo4j_db.advanced_queries import main as advanced_main
    advanced_main()
    pause()


def neo4j_menu():
    """Neo4j operations submenu."""
    options = [
        "Schema Setup (Constraints & Indexes)",
        "Seed Data (Create 50+ nodes & 60+ relationships)",
        "CRUD Operations",
        "Graph Traversal Queries",
        "Advanced Cypher Queries",
        "Full Neo4j Demo (run everything in sequence)",
    ]

    while True:
        choice = print_menu("Neo4j Operations", options)
        if choice == 0:
            break
        elif choice == 1:
            neo4j_schema_demo()
        elif choice == 2:
            neo4j_seed_demo()
        elif choice == 3:
            neo4j_crud_demo()
        elif choice == 4:
            neo4j_traversal_demo()
        elif choice == 5:
            neo4j_advanced_demo()
        elif choice == 6:
            print_header("FULL Neo4j DEMO")
            neo4j_schema_demo()
            neo4j_seed_demo()
            neo4j_crud_demo()
            neo4j_traversal_demo()
            neo4j_advanced_demo()


# ─── Main Menu ──────────────────────────────────────────────────────────────

def main():
    """Main entry point for the demo CLI."""
    print("\n+" + "=" * 58 + "+")
    print("|" + " " * 58 + "|")
    print("|   Online Learning Portal - DBMS NoSQL Project Demo       |")
    print("|   MongoDB + Neo4j Hybrid Database System                 |")
    print("|   Review 2: Implementation & Demonstration               |")
    print("|" + " " * 58 + "|")
    print("+" + "=" * 58 + "+")

    options = [
        "MongoDB Operations",
        "Neo4j Operations",
        "Full Demo (MongoDB + Neo4j)",
    ]

    try:
        while True:
            choice = print_menu("Main Menu", options)
            if choice == 0:
                print("\n  Goodbye! Closing database connections...")
                close_connections()
                break
            elif choice == 1:
                mongo_menu()
            elif choice == 2:
                neo4j_menu()
            elif choice == 3:
                print_header("FULL PROJECT DEMO")
                print("  Running complete MongoDB demo...")
                mongo_schema_demo()
                mongo_seed_demo()
                mongo_indexing_demo()
                from mongo.aggregation import (
                    avg_completion_per_course, top_students_by_completions,
                    course_revenue_analysis, quiz_performance_analysis,
                    materials_count_by_type,
                )
                print_header("MongoDB: All Aggregation Pipelines")
                avg_completion_per_course()
                top_students_by_completions()
                course_revenue_analysis()
                quiz_performance_analysis()
                materials_count_by_type()

                print("\n  Running complete Neo4j demo...")
                neo4j_schema_demo()
                neo4j_seed_demo()
                neo4j_crud_demo()
                neo4j_traversal_demo()
                neo4j_advanced_demo()

                print_header("DEMO COMPLETE")
                print("  All operations executed successfully!")
                pause()

    except KeyboardInterrupt:
        print("\n\n  Interrupted. Closing connections...")
        close_connections()


if __name__ == "__main__":
    main()
