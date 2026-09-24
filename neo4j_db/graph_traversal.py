"""
Neo4j Graph Traversal Queries for Online Learning Portal
=========================================================
Demonstrates the power of graph databases through traversal queries
that would be expensive or impossible in relational / document stores.

Functions:
    1. find_course_prerequisites  – variable-length path traversal
    2. find_learning_path         – shortest path between two courses
    3. recommend_courses          – collaborative filtering via Cypher
    4. find_students_with_common_courses – shared enrollment detection
    5. find_instructor_network    – students reachable through an instructor
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import get_neo4j_driver, close_connections


# ──────────────────────────────────────────────────────────────────────────────
# 1. Find Course Prerequisites (variable-length path)
# ──────────────────────────────────────────────────────────────────────────────

def find_course_prerequisites(driver, course_id):
    """Find all direct and transitive prerequisites for a given course.

    Uses a variable-length relationship pattern ``*1..`` to follow the
    PREREQUISITE_OF chain backwards to any depth.

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.
    course_id : str
        The course whose prerequisites we want.

    Returns
    -------
    list[dict]
        List of prerequisite courses with their depth level.
    """
    query = """
        MATCH path = (prereq:Course)-[:PREREQUISITE_OF*1..]->(target:Course {course_id: $course_id})
        RETURN prereq.course_id AS prerequisite_id,
               prereq.title     AS prerequisite_title,
               length(path)     AS depth
        ORDER BY depth ASC
    """
    results = []
    with driver.session() as session:
        records = session.run(query, course_id=course_id)
        for rec in records:
            results.append({
                "prerequisite_id":    rec["prerequisite_id"],
                "prerequisite_title": rec["prerequisite_title"],
                "depth":              rec["depth"],
            })
    return results


# ──────────────────────────────────────────────────────────────────────────────
# 2. Find Learning Path (shortest path)
# ──────────────────────────────────────────────────────────────────────────────

def find_learning_path(driver, start_course_id, end_course_id):
    """Find the shortest prerequisite path from one course to another.

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.
    start_course_id : str
        Starting course in the chain.
    end_course_id : str
        Destination course.

    Returns
    -------
    list[dict]
        Ordered list of courses in the learning path, or an empty list
        if no path exists.
    """
    query = """
        MATCH (start:Course {course_id: $start_course_id}),
              (end:Course   {course_id: $end_course_id}),
              path = shortestPath((start)-[:PREREQUISITE_OF*]->(end))
        RETURN [node IN nodes(path) |
                {course_id: node.course_id, title: node.title}
               ] AS learning_path
    """
    with driver.session() as session:
        result = session.run(
            query,
            start_course_id=start_course_id,
            end_course_id=end_course_id,
        )
        record = result.single()
        if record:
            return record["learning_path"]
    return []


# ──────────────────────────────────────────────────────────────────────────────
# 3. Recommend Courses (collaborative filtering)
# ──────────────────────────────────────────────────────────────────────────────

def recommend_courses(driver, student_id):
    """Recommend courses based on collaborative filtering.

    Logic: find other students who are enrolled in the same courses as the
    target student, then suggest courses *those* students are enrolled in
    but the target student is not.

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.
    student_id : str
        Student to generate recommendations for.

    Returns
    -------
    list[dict]
        Recommended courses with a relevance score (number of similar
        students also enrolled).
    """
    query = """
        MATCH (s:Student {student_id: $student_id})-[:ENROLLED_IN]->(c:Course)
              <-[:ENROLLED_IN]-(other:Student)-[:ENROLLED_IN]->(rec:Course)
        WHERE NOT (s)-[:ENROLLED_IN]->(rec)
          AND NOT (s)-[:COMPLETED]->(rec)
          AND s <> other
        RETURN rec.course_id   AS course_id,
               rec.title       AS title,
               rec.category    AS category,
               COUNT(DISTINCT other) AS similar_students
        ORDER BY similar_students DESC
    """
    results = []
    with driver.session() as session:
        records = session.run(query, student_id=student_id)
        for rec in records:
            results.append({
                "course_id":        rec["course_id"],
                "title":            rec["title"],
                "category":         rec["category"],
                "similar_students": rec["similar_students"],
            })
    return results


# ──────────────────────────────────────────────────────────────────────────────
# 4. Find Students with Common Courses
# ──────────────────────────────────────────────────────────────────────────────

def find_students_with_common_courses(driver, student_id):
    """Find students who share at least one enrolled course with the given student.

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.
    student_id : str
        Target student.

    Returns
    -------
    list[dict]
        Other students and the courses they share.
    """
    query = """
        MATCH (s:Student {student_id: $student_id})-[:ENROLLED_IN]->(c:Course)
              <-[:ENROLLED_IN]-(other:Student)
        WHERE s <> other
        RETURN other.student_id AS student_id,
               other.name       AS name,
               COLLECT(c.title) AS common_courses,
               COUNT(c)         AS shared_count
        ORDER BY shared_count DESC
    """
    results = []
    with driver.session() as session:
        records = session.run(query, student_id=student_id)
        for rec in records:
            results.append({
                "student_id":     rec["student_id"],
                "name":           rec["name"],
                "common_courses": list(rec["common_courses"]),
                "shared_count":   rec["shared_count"],
            })
    return results


# ──────────────────────────────────────────────────────────────────────────────
# 5. Find Instructor Network
# ──────────────────────────────────────────────────────────────────────────────

def find_instructor_network(driver, instructor_id):
    """Find all students taught by an instructor across all their courses.

    Traversal: Instructor → TEACHES → Course ← ENROLLED_IN / COMPLETED ← Student

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.
    instructor_id : str
        Instructor identifier.

    Returns
    -------
    dict
        Contains instructor info, courses taught, and a list of students
        per course.
    """
    query = """
        MATCH (i:Instructor {instructor_id: $instructor_id})-[:TEACHES]->(c:Course)
        OPTIONAL MATCH (s:Student)-[:ENROLLED_IN|COMPLETED]->(c)
        RETURN i.name            AS instructor_name,
               i.specialization AS specialization,
               c.course_id      AS course_id,
               c.title          AS course_title,
               COLLECT(DISTINCT {
                   student_id: s.student_id,
                   name:       s.name
               }) AS students
        ORDER BY c.course_id
    """
    network = {
        "instructor_name": None,
        "specialization":  None,
        "courses":         [],
    }
    with driver.session() as session:
        records = session.run(query, instructor_id=instructor_id)
        for rec in records:
            network["instructor_name"] = rec["instructor_name"]
            network["specialization"]  = rec["specialization"]
            # Filter out null student entries from OPTIONAL MATCH
            students = [
                st for st in rec["students"]
                if st.get("student_id") is not None
            ]
            network["courses"].append({
                "course_id":    rec["course_id"],
                "course_title": rec["course_title"],
                "students":     students,
            })
    return network


# ──────────────────────────────────────────────────────────────────────────────
# Pretty-print helpers
# ──────────────────────────────────────────────────────────────────────────────

def _section(title):
    """Print a section header."""
    print(f"\n{'─' * 65}")
    print(f"  {title}")
    print(f"{'─' * 65}")


# ──────────────────────────────────────────────────────────────────────────────
# Main – demonstrate all traversals
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    driver = get_neo4j_driver()

    try:
        print("\n" + "=" * 65)
        print("  Neo4j Graph Traversal Queries – Demo")
        print("=" * 65)

        # 1. Prerequisites
        _section("1. Course Prerequisites for C004 (Machine Learning A-Z)")
        prereqs = find_course_prerequisites(driver, "C004")
        if prereqs:
            for p in prereqs:
                indent = "  " * p["depth"]
                print(f"  {indent}↳ [{p['prerequisite_id']}] "
                      f"{p['prerequisite_title']}  (depth {p['depth']})")
        else:
            print("  No prerequisites found.")

        # 2. Learning Path
        _section("2. Learning Path: C001 → C004")
        path = find_learning_path(driver, "C001", "C004")
        if path:
            steps = " → ".join(
                f"[{c['course_id']}] {c['title']}" for c in path
            )
            print(f"  {steps}")
        else:
            print("  No path found between the courses.")

        # 3. Course Recommendations
        _section("3. Course Recommendations for S001 (Aarav Sharma)")
        recs = recommend_courses(driver, "S001")
        if recs:
            for r in recs:
                print(f"  📚 [{r['course_id']}] {r['title']}  "
                      f"({r['category']}) – "
                      f"{r['similar_students']} similar student(s)")
        else:
            print("  No recommendations available.")

        # 4. Common Courses
        _section("4. Students with Common Courses as S001")
        peers = find_students_with_common_courses(driver, "S001")
        if peers:
            for p in peers:
                courses_str = ", ".join(p["common_courses"])
                print(f"  👤 {p['name']} ({p['student_id']}) – "
                      f"{p['shared_count']} shared: {courses_str}")
        else:
            print("  No peers found.")

        # 5. Instructor Network
        _section("5. Instructor Network for I001 (Dr. Rajesh Kumar)")
        network = find_instructor_network(driver, "I001")
        if network["instructor_name"]:
            print(f"  Instructor: {network['instructor_name']} "
                  f"({network['specialization']})")
            for course in network["courses"]:
                print(f"\n  📖 [{course['course_id']}] {course['course_title']}")
                if course["students"]:
                    for st in course["students"]:
                        print(f"      └─ {st['name']} ({st['student_id']})")
                else:
                    print("      └─ (no students)")
        else:
            print("  Instructor not found.")

        print("\n✅ Graph traversal demo complete.\n")

    finally:
        close_connections()
