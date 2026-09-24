"""
Neo4j Advanced Queries for Online Learning Portal
===================================================
Complex Cypher queries that showcase aggregation, pattern matching,
variable-length paths, and analytical capabilities of Neo4j.

Queries:
    1. Course popularity ranking
    2. Skill gap analysis for a student
    3. Instructor workload summary
    4. Category statistics
    5. Prerequisite chain depth analysis
    6. Student completion rate
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import get_neo4j_driver, close_connections

# Optional: pretty tables if available
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


# ──────────────────────────────────────────────────────────────────────────────
# Utility
# ──────────────────────────────────────────────────────────────────────────────

def _table(headers, rows, title=None):
    """Print a list of rows as a formatted table.

    Falls back to simple column printing if *tabulate* is not installed.
    """
    if title:
        print(f"\n  {title}")
        print(f"  {'─' * (len(title) + 4)}")
    if HAS_TABULATE:
        print(tabulate(rows, headers=headers, tablefmt="fancy_grid",
                       numalign="right", stralign="left"))
    else:
        # Simple fallback
        header_line = "  " + "  ".join(f"{h:<20}" for h in headers)
        print(header_line)
        print("  " + "-" * len(header_line))
        for row in rows:
            print("  " + "  ".join(f"{str(v):<20}" for v in row))
    print()


def _section(title):
    """Print a section header."""
    print(f"\n{'=' * 65}")
    print(f"  {title}")
    print(f"{'=' * 65}")


# ──────────────────────────────────────────────────────────────────────────────
# 1. Course Popularity Ranking
# ──────────────────────────────────────────────────────────────────────────────

def course_popularity_ranking(driver):
    """Rank courses by the total number of enrolled + completed students.

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.

    Returns
    -------
    list[dict]
        Courses sorted by total student count (descending).
    """
    query = """
        MATCH (c:Course)
        OPTIONAL MATCH (s1:Student)-[:ENROLLED_IN]->(c)
        OPTIONAL MATCH (s2:Student)-[:COMPLETED]->(c)
        WITH c,
             COUNT(DISTINCT s1) AS enrolled_count,
             COUNT(DISTINCT s2) AS completed_count
        RETURN c.course_id        AS course_id,
               c.title            AS title,
               enrolled_count,
               completed_count,
               enrolled_count + completed_count AS total_students
        ORDER BY total_students DESC
    """
    results = []
    with driver.session() as session:
        for rec in session.run(query):
            results.append({
                "course_id":       rec["course_id"],
                "title":           rec["title"],
                "enrolled_count":  rec["enrolled_count"],
                "completed_count": rec["completed_count"],
                "total_students":  rec["total_students"],
            })
    return results


# ──────────────────────────────────────────────────────────────────────────────
# 2. Skill Gap Analysis
# ──────────────────────────────────────────────────────────────────────────────

def skill_gap_analysis(driver, student_id):
    """Identify skills required by a student's enrolled courses that
    the student does not yet possess.

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.
    student_id : str
        Student identifier.

    Returns
    -------
    list[dict]
        Missing skills and the courses that require them.
    """
    query = """
        MATCH (s:Student {student_id: $student_id})-[:ENROLLED_IN]->(c:Course)
              -[:REQUIRES_SKILL]->(sk:Skill)
        WHERE NOT (s)-[:HAS_SKILL]->(sk)
        RETURN sk.skill_id          AS skill_id,
               sk.name              AS skill_name,
               COLLECT(c.title)     AS required_by_courses,
               COUNT(DISTINCT c)    AS course_count
        ORDER BY course_count DESC
    """
    results = []
    with driver.session() as session:
        for rec in session.run(query, student_id=student_id):
            results.append({
                "skill_id":            rec["skill_id"],
                "skill_name":          rec["skill_name"],
                "required_by_courses": list(rec["required_by_courses"]),
                "course_count":        rec["course_count"],
            })
    return results


# ──────────────────────────────────────────────────────────────────────────────
# 3. Instructor Workload
# ──────────────────────────────────────────────────────────────────────────────

def instructor_workload(driver):
    """Calculate the number of courses and total students per instructor.

    Uses COLLECT to aggregate course titles.

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.

    Returns
    -------
    list[dict]
        Instructor workload summaries sorted by student count.
    """
    query = """
        MATCH (i:Instructor)-[:TEACHES]->(c:Course)
        OPTIONAL MATCH (s:Student)-[:ENROLLED_IN|COMPLETED]->(c)
        WITH i,
             COLLECT(DISTINCT c.title)       AS courses_taught,
             COUNT(DISTINCT c)               AS course_count,
             COUNT(DISTINCT s)               AS student_count
        RETURN i.instructor_id  AS instructor_id,
               i.name           AS name,
               i.rating         AS rating,
               course_count,
               courses_taught,
               student_count
        ORDER BY student_count DESC
    """
    results = []
    with driver.session() as session:
        for rec in session.run(query):
            results.append({
                "instructor_id": rec["instructor_id"],
                "name":          rec["name"],
                "rating":        rec["rating"],
                "course_count":  rec["course_count"],
                "courses_taught": list(rec["courses_taught"]),
                "student_count": rec["student_count"],
            })
    return results


# ──────────────────────────────────────────────────────────────────────────────
# 4. Category Statistics
# ──────────────────────────────────────────────────────────────────────────────

def category_statistics(driver):
    """Compute per-category statistics: course count, average difficulty
    (mapped to numeric), and total enrolled students.

    Uses OPTIONAL MATCH so categories with no courses still appear.

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.

    Returns
    -------
    list[dict]
        Category-level statistics.
    """
    query = """
        MATCH (cat:Category)
        OPTIONAL MATCH (c:Course)-[:BELONGS_TO]->(cat)
        OPTIONAL MATCH (s:Student)-[:ENROLLED_IN]->(c)
        WITH cat,
             COUNT(DISTINCT c) AS course_count,
             COLLECT(DISTINCT c.difficulty_level) AS difficulty_levels,
             AVG(c.duration_hours) AS avg_duration,
             COUNT(DISTINCT s) AS total_enrolled
        RETURN cat.name         AS category,
               cat.description  AS description,
               course_count,
               difficulty_levels,
               ROUND(COALESCE(avg_duration, 0), 1) AS avg_duration_hours,
               total_enrolled
        ORDER BY course_count DESC
    """
    results = []
    with driver.session() as session:
        for rec in session.run(query):
            results.append({
                "category":           rec["category"],
                "description":        rec["description"],
                "course_count":       rec["course_count"],
                "difficulty_levels":  list(rec["difficulty_levels"]),
                "avg_duration_hours": rec["avg_duration_hours"],
                "total_enrolled":     rec["total_enrolled"],
            })
    return results


# ──────────────────────────────────────────────────────────────────────────────
# 5. Prerequisite Chain Depth
# ──────────────────────────────────────────────────────────────────────────────

def prerequisite_chain_depth(driver):
    """Find courses and the depth of their longest prerequisite chain.

    Courses with no prerequisites have depth 0.

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.

    Returns
    -------
    list[dict]
        Courses sorted by chain depth (deepest first).
    """
    query = """
        MATCH (c:Course)
        OPTIONAL MATCH path = (prereq:Course)-[:PREREQUISITE_OF*1..]->(c)
        WITH c,
             coalesce(max(length(path)), 0) AS chain_depth,
             COLLECT(DISTINCT prereq.title) AS prerequisites
        RETURN c.course_id  AS course_id,
               c.title      AS title,
               chain_depth,
               prerequisites
        ORDER BY chain_depth DESC, c.course_id ASC
    """
    results = []
    with driver.session() as session:
        for rec in session.run(query):
            # Filter out null entries in prerequisites
            prereqs = [p for p in rec["prerequisites"] if p is not None]
            results.append({
                "course_id":     rec["course_id"],
                "title":         rec["title"],
                "chain_depth":   rec["chain_depth"],
                "prerequisites": prereqs,
            })
    return results


# ──────────────────────────────────────────────────────────────────────────────
# 6. Student Completion Rate
# ──────────────────────────────────────────────────────────────────────────────

def student_completion_rate(driver):
    """Calculate the percentage of enrolled courses each student has completed.

    Parameters
    ----------
    driver : neo4j.Driver
        Active Neo4j driver.

    Returns
    -------
    list[dict]
        Students with their enrolled count, completed count, and
        completion percentage.
    """
    query = """
        MATCH (s:Student)
        OPTIONAL MATCH (s)-[:ENROLLED_IN]->(enrolled:Course)
        OPTIONAL MATCH (s)-[:COMPLETED]->(completed:Course)
        WITH s,
             COUNT(DISTINCT enrolled)  AS enrolled_count,
             COUNT(DISTINCT completed) AS completed_count
        RETURN s.student_id   AS student_id,
               s.name         AS name,
               enrolled_count,
               completed_count,
               CASE WHEN enrolled_count + completed_count = 0 THEN 0.0
                    ELSE ROUND(
                        toFloat(completed_count) * 100.0
                        / toFloat(enrolled_count + completed_count), 1
                    )
               END AS completion_pct
        ORDER BY completion_pct DESC
    """
    results = []
    with driver.session() as session:
        for rec in session.run(query):
            results.append({
                "student_id":     rec["student_id"],
                "name":           rec["name"],
                "enrolled_count": rec["enrolled_count"],
                "completed_count": rec["completed_count"],
                "completion_pct": rec["completion_pct"],
            })
    return results


def main(driver=None):
    """Run all Neo4j advanced query demonstrations."""
    should_close = False
    if driver is None:
        driver = get_neo4j_driver()
        should_close = True

    try:
        print("\n" + "=" * 65)
        print("  Neo4j Advanced Queries – Demo")
        print("=" * 65)

        # ── 1. Course Popularity ─────────────────────────────────────────
        _section("1. Course Popularity Ranking")
        ranking = course_popularity_ranking(driver)
        headers = ["Course ID", "Title", "Enrolled", "Completed", "Total"]
        rows = [
            [r["course_id"], r["title"], r["enrolled_count"],
             r["completed_count"], r["total_students"]]
            for r in ranking
        ]
        _table(headers, rows)

        # ── 2. Skill Gap Analysis ────────────────────────────────────────
        _section("2. Skill Gap Analysis for S001 (Aarav Sharma)")
        gaps = skill_gap_analysis(driver, "S001")
        if gaps:
            for g in gaps:
                courses = ", ".join(g["required_by_courses"])
                print(f"  ⚠  Missing: {g['skill_name']} (ID: {g['skill_id']})")
                print(f"     Required by: {courses}\n")
        else:
            print("  ✔ No skill gaps – student has all required skills!")

        # ── 3. Instructor Workload ───────────────────────────────────────
        _section("3. Instructor Workload")
        workloads = instructor_workload(driver)
        for w in workloads:
            courses = ", ".join(w["courses_taught"])
            print(f"  👨‍🏫 {w['name']} ({w['instructor_id']}) "
                  f"– Rating: {w['rating']}")
            print(f"     Courses ({w['course_count']}): {courses}")
            print(f"     Total students: {w['student_count']}\n")

        # ── 4. Category Statistics ───────────────────────────────────────
        _section("4. Category Statistics")
        cat_stats = category_statistics(driver)
        headers = ["Category", "Courses", "Avg Duration (hrs)",
                   "Enrolled Students", "Difficulty Levels"]
        rows = [
            [c["category"], c["course_count"], c["avg_duration_hours"],
             c["total_enrolled"], ", ".join(c["difficulty_levels"])]
            for c in cat_stats
        ]
        _table(headers, rows)

        # ── 5. Prerequisite Chain Depth ──────────────────────────────────
        _section("5. Prerequisite Chain Depth")
        chains = prerequisite_chain_depth(driver)
        headers = ["Course ID", "Title", "Chain Depth", "Prerequisites"]
        rows = [
            [c["course_id"], c["title"], c["chain_depth"],
             ", ".join(c["prerequisites"]) if c["prerequisites"] else "—"]
            for c in chains
        ]
        _table(headers, rows)

        # ── 6. Student Completion Rate ───────────────────────────────────
        _section("6. Student Completion Rate")
        rates = student_completion_rate(driver)
        headers = ["Student ID", "Name", "Enrolled", "Completed", "Rate (%)"]
        rows = [
            [r["student_id"], r["name"], r["enrolled_count"],
             r["completed_count"], f"{r['completion_pct']}%"]
            for r in rates
        ]
        _table(headers, rows)

        print("\n✅ Advanced queries demo complete.\n")

    finally:
        if should_close:
            close_connections()


# ──────────────────────────────────────────────────────────────────────────────
# Main – execute and display all advanced queries
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
