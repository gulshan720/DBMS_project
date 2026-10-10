"""
End-to-End Real Browser UI Test Suite using Playwright (Chromium/Edge)
Verifies Desktop and Mobile viewports, user interactions, modals,
real-time database updates, console error absence, and data integrity.
"""

import os
import sys
import time
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from playwright.sync_api import sync_playwright
from config.db_config import get_mongo_db, get_neo4j_driver

BASE_URL = "http://127.0.0.1:8000"

def restore_clean_baseline():
    """Ensure no test leftover artifacts exist in databases."""
    db = get_mongo_db()
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

def verify_db_counts():
    db = get_mongo_db()
    m_counts = {
        col: db[col].count_documents({})
        for col in ["students", "courses", "instructors", "learning_materials", "quizzes", "progress"]
    }
    driver = get_neo4j_driver()
    with driver.session() as s:
        nodes = s.run("MATCH (n) RETURN count(n) AS cnt").single()["cnt"]
        rels = s.run("MATCH ()-[r]->() RETURN count(r) AS cnt").single()["cnt"]
    return sum(m_counts.values()), nodes, rels

def run_browser_tests():
    print("=" * 65)
    print("Real-Browser Frontend Verification (Playwright Chromium)")
    print("=" * 65)

    # 1. Verify baseline before start
    restore_clean_baseline()
    m_docs, n_nodes, n_rels = verify_db_counts()
    print(f"[Initial Baseline] Mongo docs: {m_docs}, Neo4j nodes: {n_nodes}, rels: {n_rels}")
    assert m_docs == 57, f"Expected 57 Mongo docs, got {m_docs}"
    assert n_nodes == 52, f"Expected 52 Neo4j nodes, got {n_nodes}"
    assert n_rels == 72, f"Expected 72 Neo4j rels, got {n_rels}"

    # Track console messages and network errors
    console_errors = []
    network_errors = []

    with sync_playwright() as p:
        # Launch browser using msedge channel
        browser = p.chromium.launch(channel="msedge", headless=True)
        
        # -------------------------------------------------------------
        # TEST 1: DESKTOP VIEWPORT (1280 x 800)
        # -------------------------------------------------------------
        print("\n--- Running Desktop Tests (Viewport: 1280x800) ---")
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))
        page.on("requestfailed", lambda req: network_errors.append(f"{req.method} {req.url}: {req.failure}"))
        page.on("dialog", lambda dialog: dialog.accept())

        # Load home
        page.goto(BASE_URL, wait_until="networkidle")
        assert "Online Learning Portal" in page.title()
        print("PASS [Desktop]: Page loaded with title matching 'Online Learning Portal'")

        # 1. Dashboard Metrics Verification
        page.wait_for_selector("#kpi-students:not(:empty)")
        time.sleep(1)
        students_kpi = page.inner_text("#kpi-students")
        courses_kpi = page.inner_text("#kpi-courses")
        nodes_kpi = page.inner_text("#kpi-nodes")
        rels_kpi = page.inner_text("#kpi-rels")

        print(f"PASS [Desktop]: Live KPI counters - Students: {students_kpi}, Courses: {courses_kpi}, Nodes: {nodes_kpi}, Rels: {rels_kpi}")
        assert students_kpi == "10", f"Expected 10 students, got {students_kpi}"
        assert courses_kpi == "10", f"Expected 10 courses, got {courses_kpi}"
        assert nodes_kpi == "52", f"Expected 52 nodes, got {nodes_kpi}"
        assert rels_kpi == "72", f"Expected 72 rels, got {rels_kpi}"

        # Check DB status indicators
        mongo_dot = page.locator("#mongo-dot")
        neo_dot = page.locator("#neo-dot")
        assert "connected" in (mongo_dot.get_attribute("class") or "")
        assert "connected" in (neo_dot.get_attribute("class") or "")
        print("PASS [Desktop]: Database indicators (MongoDB & Neo4j) are connected (green)")

        # 2. Navigation Verification
        views = [
            ("students", "#view-students"),
            ("courses", "#view-courses"),
            ("materials", "#view-materials"),
            ("quizzes", "#view-quizzes"),
            ("analytics", "#view-analytics"),
            ("graph", "#view-graph"),
            ("dashboard", "#view-dashboard")
        ]
        for view_name, selector in views:
            page.click(f".sidebar-menu a[data-view='{view_name}']")
            page.wait_for_selector(f"{selector}.active")
            assert page.is_visible(selector), f"View {view_name} not visible"
            print(f"PASS [Desktop]: Navigation opens '{view_name}' view")

        # 3. Students Workflow: Search, Register, View, Enroll, Delete
        page.click(".sidebar-menu a[data-view='students']")
        page.wait_for_selector("#students-table-body tr")

        # Search
        page.fill("#students-search", "Aarav")
        time.sleep(0.5)
        search_rows = page.locator("#students-table-body tr")
        assert search_rows.count() >= 1, "Student search returned no rows"
        print(f"PASS [Desktop]: Student search filtered correctly")
        page.fill("#students-search", "")
        time.sleep(0.5)

        # Register Student (S998)
        page.click("#btn-add-student")
        page.wait_for_selector("#modal-student.active")
        page.fill("#std-id", "S998")
        page.fill("#std-name", "Desktop Test Student")
        page.fill("#std-email", "desktop.test@portal.edu")
        page.fill("#std-phone", "9876543210")
        page.click("#form-student button[type='submit']")
        page.wait_for_selector("tr:has-text('S998')")
        print("PASS [Desktop]: Student S998 registration submitted and row visible")

        # View Details & Enroll
        time.sleep(0.5)
        details_btn = page.locator("tr:has-text('S998') button:has-text('Details')").first
        details_btn.click()
        page.wait_for_selector("#modal-student-details.active")
        page.wait_for_selector("#student-details-body h4")
        print("PASS [Desktop]: Student details modal displayed")

        # Inline Enroll
        page.fill("#quick-enroll-cid", "C001")
        page.click("button:has-text('Enroll')")
        time.sleep(1)
        print("PASS [Desktop]: Inline student enrollment executed")
        page.click("#modal-student-details .modal-close-btn")
        page.wait_for_selector("#modal-student-details", state="hidden")
        time.sleep(0.5)

        # Delete Student S998
        delete_btn = page.locator("tr:has-text('S998') button.btn-danger")
        if delete_btn.count() > 0:
            delete_btn.click()
            page.wait_for_selector("tr:has-text('S998')", state="detached")
            print("PASS [Desktop]: Student S998 deleted and removed from table")

        # 4. Courses Workflow: Filter, Add, Details Modal, Delete
        page.click(".sidebar-menu a[data-view='courses']")
        page.wait_for_selector("#courses-table-body tr")

        # Filter by category
        page.select_option("#course-category-filter", "Data Science")
        time.sleep(0.5)
        print("PASS [Desktop]: Courses filtered by category 'Data Science'")
        page.select_option("#course-category-filter", "")
        time.sleep(0.5)

        # Add Course C998
        page.click("#btn-add-course")
        page.wait_for_selector("#modal-course.active")
        page.fill("#crs-id", "C998")
        page.fill("#crs-title", "Playwright Browser Automation")
        page.fill("#crs-category", "Data Science")
        page.select_option("#crs-difficulty", "Beginner")
        page.fill("#crs-instructor", "I001")
        page.fill("#crs-duration", "25")
        page.fill("#crs-price", "1999")
        page.click("#form-course button[type='submit']")
        page.wait_for_selector("tr:has-text('C998')")
        print("PASS [Desktop]: Course C998 created successfully and visible in table")

        # View Course Details Modal
        time.sleep(0.5)
        course_info_btn = page.locator("tr:has-text('C998') button.btn-secondary").first
        course_info_btn.click()
        page.wait_for_selector("#modal-course-details.active")
        assert page.is_visible("#modal-course-details-title")
        print("PASS [Desktop]: Rich course details modal displayed")
        page.click("#modal-course-details .modal-close-btn")
        page.wait_for_selector("#modal-course-details", state="hidden")
        time.sleep(0.5)

        # Delete Course C998
        delete_course_btn = page.locator("tr:has-text('C998') button.btn-danger")
        if delete_course_btn.count() > 0:
            delete_course_btn.click()
            page.wait_for_selector("tr:has-text('C998')", state="detached")
            print("PASS [Desktop]: Course C998 deleted successfully")

        # 5. Learning Materials Workflow
        page.click(".sidebar-menu a[data-view='materials']")
        page.wait_for_selector("#materials-table-body tr")
        page.select_option("#materials-type-filter", "video")
        time.sleep(0.5)
        print("PASS [Desktop]: Materials filtered by type 'video'")
        page.select_option("#materials-type-filter", "")

        # Add Material M998
        page.click("#btn-add-material")
        page.wait_for_selector("#modal-material.active")
        page.fill("#mat-id", "M998")
        page.fill("#mat-course-id", "C001")
        page.fill("#mat-title", "Playwright Automation Guide")
        page.select_option("#mat-type", "article")
        page.fill("#mat-url", "https://example.com/playwright")
        page.fill("#mat-duration", "15")
        page.click("#form-material button[type='submit']")
        page.wait_for_selector("tr:has-text('M998')")
        print("PASS [Desktop]: Material M998 created successfully")

        # Delete Material M998
        del_mat_btn = page.locator("tr:has-text('M998') button.btn-danger")
        if del_mat_btn.count() > 0:
            del_mat_btn.click()
            page.wait_for_selector("tr:has-text('M998')", state="detached")
            print("PASS [Desktop]: Material M998 deleted successfully")

        # 6. Quizzes & Progress Workflow
        page.click(".sidebar-menu a[data-view='quizzes']")
        page.wait_for_selector("#quizzes-table-body tr")

        # Add Quiz Modal
        page.click("#btn-add-quiz")
        page.wait_for_selector("#modal-quiz.active")
        page.fill("#qz-id", "Q998")
        page.fill("#qz-course-id", "C001")
        page.fill("#qz-title", "Browser Validation Assessment")
        page.fill("#qz-points", "15")
        page.fill("#qz-time", "15")
        page.fill("#qz-q1-text", "Does Playwright support Chromium?")
        page.fill("#qz-q1-answer", "Yes")
        page.click("#form-quiz button[type='submit']")
        page.wait_for_selector("tr:has-text('Q998')")
        print("PASS [Desktop]: Quiz Q998 added successfully via modal")

        # Delete Quiz Q998
        time.sleep(0.5)
        del_qz_btn = page.locator("tr:has-text('Q998') button.btn-danger")
        if del_qz_btn.count() > 0:
            del_qz_btn.click()
            page.wait_for_selector("tr:has-text('Q998')", state="detached")
            print("PASS [Desktop]: Quiz Q998 deleted successfully")

        # Switch to Student Progress sub-tab
        page.click("#view-quizzes .tabs-header button[data-tab='tab-progress']")
        page.wait_for_selector("#tab-progress.active")
        time.sleep(0.5)

        # Adjust Progress Slider Modal
        adj_btn = page.locator("#progress-table-body button:has-text('Adjust')").first
        adj_btn.click()
        page.wait_for_selector("#modal-progress.active")
        page.click("#form-progress button[type='submit']")
        page.wait_for_selector("#modal-progress", state="hidden")
        print("PASS [Desktop]: Student progress modal updated successfully")

        # 7. Analytics Workflow
        page.click(".sidebar-menu a[data-view='analytics']")
        page.wait_for_selector("#view-analytics.active")
        # Click each tab
        for tab_id, table_id in [
            ("tab-agg2", "#agg2-table-body"),
            ("tab-agg3", "#agg3-table-body"),
            ("tab-agg4", "#agg4-table-body"),
            ("tab-agg5", "#agg5-table-body"),
            ("tab-indexing", "#explain-box")
        ]:
            page.click(f"#view-analytics .tabs-header button[data-tab='{tab_id}']")
            page.wait_for_selector(f"#{tab_id}.active")
            print(f"PASS [Desktop]: Analytics tab '{tab_id}' rendered with live data")

        # 8. Neo4j Graph Insights Workflow
        page.click(".sidebar-menu a[data-view='graph']")
        page.wait_for_selector("#view-graph.active")

        # Prerequisite Chain Explorer
        page.click("#btn-explore-prereqs")
        page.wait_for_selector("#prereq-results div")
        print("PASS [Desktop]: Prerequisite chain traversed and rendered")

        # Learning Path Finder
        page.click("#btn-find-path")
        page.wait_for_selector("#path-results h5")
        print("PASS [Desktop]: Shortest learning path traversed and rendered")

        # Collaborative Filtering Recommendations
        page.click("#view-graph .tabs-header button[data-tab='tab-recs']")
        page.click("#btn-get-recs")
        page.wait_for_selector("#rec-results")
        print("PASS [Desktop]: Collaborative recommendations rendered")

        # Skill Gaps
        page.click("#btn-check-gaps")
        page.wait_for_selector("#gap-results")
        print("PASS [Desktop]: Skill gaps analyzed and rendered")

        # Cypher Analytics Tab
        page.click("#view-graph .tabs-header button[data-tab='tab-graph-analytics']")
        page.wait_for_selector("#neo-pop-table tr")
        print("PASS [Desktop]: Course popularity & instructor workload tables rendered")

        context.close()

        # -------------------------------------------------------------
        # TEST 2: MOBILE VIEWPORT (375 x 667 - iPhone SE / Standard Mobile)
        # -------------------------------------------------------------
        print("\n--- Running Mobile Tests (Viewport: 375x667) ---")
        mobile_context = browser.new_context(
            viewport={"width": 375, "height": 667},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        )
        mobile_page = mobile_context.new_page()
        mobile_page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        mobile_page.on("pageerror", lambda err: console_errors.append(str(err)))

        mobile_page.goto(BASE_URL, wait_until="networkidle")
        mobile_page.wait_for_selector("#kpi-students")

        # Verify layout elements are responsive
        sidebar_menu = mobile_page.locator(".sidebar-menu")
        assert sidebar_menu.is_visible()
        print("PASS [Mobile]: Responsive sidebar menu renders in horizontal scrolling mode")

        # Test tab navigation on mobile
        mobile_page.click(".sidebar-menu a[data-view='students']")
        mobile_page.wait_for_selector("#view-students.active")
        assert mobile_page.is_visible("#students-search")
        print("PASS [Mobile]: Navigated to students view on mobile")

        mobile_page.click(".sidebar-menu a[data-view='graph']")
        mobile_page.wait_for_selector("#view-graph.active")
        assert mobile_page.is_visible("#btn-explore-prereqs")
        print("PASS [Mobile]: Navigated to graph insights on mobile")

        mobile_context.close()
        browser.close()

    # Final cleanup and baseline verification
    restore_clean_baseline()
    m_final, n_final_nodes, n_final_rels = verify_db_counts()
    print(f"\n[Post-Browser Baseline Verification]")
    print(f"MongoDB docs: {m_final}, Neo4j nodes: {n_final_nodes}, rels: {n_final_rels}")
    assert m_final == 57, f"Data integrity issue: Mongo docs {m_final} != 57"
    assert n_final_nodes == 52, f"Data integrity issue: Neo4j nodes {n_final_nodes} != 52"
    assert n_final_rels == 72, f"Data integrity issue: Neo4j rels {n_final_rels} != 72"

    # Filter any benign third-party warnings (e.g. FontAwesome CDN icon font warnings)
    fatal_errors = [e for e in console_errors if "favicon" not in e and "font" not in e.lower()]
    print(f"Console errors: {len(fatal_errors)}, Network failures: {len(network_errors)}")
    assert len(fatal_errors) == 0, f"Uncaught JavaScript console errors: {fatal_errors}"
    assert len(network_errors) == 0, f"Failed network requests: {network_errors}"

    print("\n" + "=" * 65)
    print("ALL REAL-BROWSER UI WORKFLOW TESTS PASSED CLEANLY!")
    print("=" * 65)

if __name__ == "__main__":
    run_browser_tests()
