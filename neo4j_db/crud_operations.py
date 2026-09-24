"""
Neo4j CRUD Operations for Online Learning Portal
==================================================
Provides Create, Read, Update, Delete operations on the graph database
via parameterized Cypher queries.

Functions:
    - create_student          – Create a new Student node
    - get_student             – Retrieve a student and their enrolled courses
    - update_student_email    – Update a student's email address
    - delete_student          – Delete a student node and all its relationships
    - create_enrollment       – Enroll a student in a course
    - remove_enrollment       – Remove an enrollment relationship
    - mark_course_completed   – Mark a course as completed with a grade
"""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import get_neo4j_driver, close_connections


# ──────────────────────────────────────────────────────────────────────────────
# CREATE
# ──────────────────────────────────────────────────────────────────────────────

def create_student(driver, student_id, name, email, enrollment_date=None):
    """Create a new Student node in the graph.

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.
    student_id : str
        Unique student identifier (e.g. "S011").
    name : str
        Full name of the student.
    email : str
        Email address.
    enrollment_date : str, optional
        ISO date string. Defaults to today's date.

    Returns
    -------
    dict or None
        The created student's properties, or None on failure.
    """
    if enrollment_date is None:
        enrollment_date = date.today().isoformat()

    query = """
        CREATE (s:Student {
            student_id:      $student_id,
            name:            $name,
            email:           $email,
            enrollment_date: $enrollment_date
        })
        RETURN s
    """
    with driver.session() as session:
        result = session.run(
            query,
            student_id=student_id,
            name=name,
            email=email,
            enrollment_date=enrollment_date,
        )
        record = result.single()
        if record:
            node = record["s"]
            print(f"  ✔ Created student: {dict(node)}")
            return dict(node)
        print("  ✘ Student creation failed.")
        return None


# ──────────────────────────────────────────────────────────────────────────────
# READ
# ──────────────────────────────────────────────────────────────────────────────

def get_student(driver, student_id):
    """Retrieve a student and all courses they are enrolled in.

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.
    student_id : str
        Student identifier.

    Returns
    -------
    dict or None
        Dictionary with 'student' properties and a list of 'enrolled_courses',
        or None if the student is not found.
    """
    query = """
        MATCH (s:Student {student_id: $student_id})
        OPTIONAL MATCH (s)-[e:ENROLLED_IN]->(c:Course)
        RETURN s,
               COLLECT({
                   course_id:       c.course_id,
                   title:           c.title,
                   enrollment_date: e.enrollment_date,
                   status:          e.status
               }) AS enrolled_courses
    """
    with driver.session() as session:
        result = session.run(query, student_id=student_id)
        record = result.single()
        if record and record["s"] is not None:
            student_data = dict(record["s"])
            # Filter out empty course entries from OPTIONAL MATCH
            courses = [
                c for c in record["enrolled_courses"]
                if c.get("course_id") is not None
            ]
            return {"student": student_data, "enrolled_courses": courses}
        return None


# ──────────────────────────────────────────────────────────────────────────────
# UPDATE
# ──────────────────────────────────────────────────────────────────────────────

def update_student_email(driver, student_id, new_email):
    """Update the email address of an existing student.

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.
    student_id : str
        Student identifier.
    new_email : str
        New email address.

    Returns
    -------
    dict or None
        Updated student properties, or None if student not found.
    """
    query = """
        MATCH (s:Student {student_id: $student_id})
        SET s.email = $new_email
        RETURN s
    """
    with driver.session() as session:
        result = session.run(query, student_id=student_id, new_email=new_email)
        record = result.single()
        if record:
            updated = dict(record["s"])
            print(f"  ✔ Updated email for {student_id}: {updated['email']}")
            return updated
        print(f"  ✘ Student {student_id} not found.")
        return None


# ──────────────────────────────────────────────────────────────────────────────
# DELETE
# ──────────────────────────────────────────────────────────────────────────────

def delete_student(driver, student_id):
    """Delete a student node and all its relationships.

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.
    student_id : str
        Student identifier.

    Returns
    -------
    bool
        True if a student was deleted, False otherwise.
    """
    query = """
        MATCH (s:Student {student_id: $student_id})
        DETACH DELETE s
    """
    with driver.session() as session:
        result = session.run(query, student_id=student_id)
        summary = result.consume()
        deleted = summary.counters.nodes_deleted
        if deleted > 0:
            print(f"  ✔ Deleted student {student_id} "
                  f"(+ {summary.counters.relationships_deleted} relationships)")
            return True
        print(f"  ✘ Student {student_id} not found.")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# ENROLLMENT OPERATIONS
# ──────────────────────────────────────────────────────────────────────────────

def create_enrollment(driver, student_id, course_id, enrollment_date=None,
                      status="active"):
    """Enroll a student in a course by creating an ENROLLED_IN relationship.

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.
    student_id : str
        Student identifier.
    course_id : str
        Course identifier.
    enrollment_date : str, optional
        ISO date string. Defaults to today.
    status : str, optional
        Enrollment status (default "active").

    Returns
    -------
    bool
        True if the enrollment was created.
    """
    if enrollment_date is None:
        enrollment_date = date.today().isoformat()

    query = """
        MATCH (s:Student {student_id: $student_id}),
              (c:Course  {course_id:  $course_id})
        MERGE (s)-[r:ENROLLED_IN]->(c)
        SET r.enrollment_date = $enrollment_date,
            r.status          = $status
        RETURN s.student_id AS sid, c.title AS title
    """
    with driver.session() as session:
        result = session.run(
            query,
            student_id=student_id,
            course_id=course_id,
            enrollment_date=enrollment_date,
            status=status,
        )
        record = result.single()
        if record:
            print(f"  ✔ Enrolled {record['sid']} → {record['title']}")
            return True
        print(f"  ✘ Could not enroll {student_id} in {course_id} "
              "(check IDs exist).")
        return False


def remove_enrollment(driver, student_id, course_id):
    """Remove the ENROLLED_IN relationship between a student and a course.

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.
    student_id : str
        Student identifier.
    course_id : str
        Course identifier.

    Returns
    -------
    bool
        True if the relationship was deleted.
    """
    query = """
        MATCH (s:Student {student_id: $student_id})
              -[r:ENROLLED_IN]->
              (c:Course {course_id: $course_id})
        DELETE r
        RETURN s.student_id AS sid, c.title AS title
    """
    with driver.session() as session:
        result = session.run(
            query, student_id=student_id, course_id=course_id
        )
        record = result.single()
        if record:
            print(f"  ✔ Removed enrollment: {record['sid']} ✗ {record['title']}")
            return True
        print(f"  ✘ No enrollment found for {student_id} in {course_id}.")
        return False


def mark_course_completed(driver, student_id, course_id, grade,
                          completion_date=None):
    """Mark a course as completed by creating / updating a COMPLETED relationship.

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.
    student_id : str
        Student identifier.
    course_id : str
        Course identifier.
    grade : str
        Grade achieved (e.g. "A", "B+").
    completion_date : str, optional
        ISO date string. Defaults to today.

    Returns
    -------
    bool
        True on success.
    """
    if completion_date is None:
        completion_date = date.today().isoformat()

    query = """
        MATCH (s:Student {student_id: $student_id}),
              (c:Course  {course_id:  $course_id})
        MERGE (s)-[r:COMPLETED]->(c)
        SET r.completion_date = $completion_date,
            r.grade           = $grade
        RETURN s.name AS name, c.title AS title
    """
    with driver.session() as session:
        result = session.run(
            query,
            student_id=student_id,
            course_id=course_id,
            grade=grade,
            completion_date=completion_date,
        )
        record = result.single()
        if record:
            print(f"  ✔ {record['name']} completed '{record['title']}' "
                  f"with grade {grade}")
            return True
        print(f"  ✘ Could not mark completion for {student_id}/{course_id}.")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Demo helpers
# ──────────────────────────────────────────────────────────────────────────────

def _print_student_details(data):
    """Pretty-print student details returned by get_student()."""
    if data is None:
        print("  (no data)")
        return
    s = data["student"]
    print(f"  Student: {s['name']}  ({s['student_id']})")
    print(f"  Email:   {s['email']}")
    print(f"  Enrolled since: {s.get('enrollment_date', 'N/A')}")
    courses = data["enrolled_courses"]
    if courses:
        print(f"  Enrolled courses ({len(courses)}):")
        for c in courses:
            print(f"    - [{c['course_id']}] {c['title']}  "
                  f"(status: {c['status']}, enrolled: {c['enrollment_date']})")
    else:
        print("  Enrolled courses: (none)")


# ──────────────────────────────────────────────────────────────────────────────
# Main – demonstrate every operation
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    driver = get_neo4j_driver()

    try:
        print("\n" + "=" * 65)
        print("  Neo4j CRUD Operations – Demo")
        print("=" * 65)

        # 1. CREATE student
        print("\n── 1. CREATE Student ──────────────────────────────────────")
        create_student(driver, "S099", "Demo Student", "demo@email.com")

        # 2. READ student (existing)
        print("\n── 2. READ Student (S001) ────────────────────────────────")
        data = get_student(driver, "S001")
        _print_student_details(data)

        # 3. READ the newly created student
        print("\n── 3. READ Student (S099 – just created) ─────────────────")
        data = get_student(driver, "S099")
        _print_student_details(data)

        # 4. UPDATE email
        print("\n── 4. UPDATE Student Email (S099) ────────────────────────")
        update_student_email(driver, "S099", "demo.updated@email.com")

        # 5. CREATE enrollment
        print("\n── 5. CREATE Enrollment (S099 → C001) ───────────────────")
        create_enrollment(driver, "S099", "C001")

        # 6. Verify enrollment
        print("\n── 6. Verify Enrollment ──────────────────────────────────")
        data = get_student(driver, "S099")
        _print_student_details(data)

        # 7. MARK course completed
        print("\n── 7. MARK Course Completed (S099 → C001, grade A) ──────")
        mark_course_completed(driver, "S099", "C001", "A")

        # 8. REMOVE enrollment
        print("\n── 8. REMOVE Enrollment (S099 → C001) ───────────────────")
        remove_enrollment(driver, "S099", "C001")

        # 9. DELETE student
        print("\n── 9. DELETE Student (S099) ──────────────────────────────")
        delete_student(driver, "S099")

        # 10. Verify deletion
        print("\n── 10. Verify Deletion ───────────────────────────────────")
        data = get_student(driver, "S099")
        if data is None:
            print("  ✔ Student S099 successfully deleted (not found).")

        print("\n✅ CRUD demo complete.\n")

    finally:
        close_connections()
