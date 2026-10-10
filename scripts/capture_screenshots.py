"""
Capture real screenshots of the Online Learning Portal using Playwright.
Saves genuine screenshots to docs/screenshots/ for README and user guide.
"""

import os
from pathlib import Path
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "screenshots"

def capture_portal_screenshots():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Saving screenshots to: {OUTPUT_DIR}")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)

        # Desktop Context (1280x800)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # 1. Dashboard
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_selector("#kpi-students:not(:empty)")
        time.sleep(1) # Allow charts and telemetry to render
        dash_path = OUTPUT_DIR / "dashboard.png"
        page.screenshot(path=str(dash_path), full_page=False)
        print(f"Captured: {dash_path}")

        # 2. Students Page
        page.click(".sidebar-menu a[data-view='students']")
        page.wait_for_selector("#students-table-body tr")
        time.sleep(0.5)
        students_path = OUTPUT_DIR / "students.png"
        page.screenshot(path=str(students_path), full_page=False)
        print(f"Captured: {students_path}")

        # 3. Courses Page
        page.click(".sidebar-menu a[data-view='courses']")
        page.wait_for_selector("#courses-table-body tr")
        time.sleep(0.5)
        courses_path = OUTPUT_DIR / "courses.png"
        page.screenshot(path=str(courses_path), full_page=False)
        print(f"Captured: {courses_path}")

        # 4. Learning Materials Page
        page.click(".sidebar-menu a[data-view='materials']")
        page.wait_for_selector("#materials-table-body tr")
        time.sleep(0.5)
        materials_path = OUTPUT_DIR / "materials.png"
        page.screenshot(path=str(materials_path), full_page=False)
        print(f"Captured: {materials_path}")

        # 5. Quizzes and Progress
        page.click(".sidebar-menu a[data-view='quizzes']")
        page.wait_for_selector("#quizzes-table-body tr")
        time.sleep(0.5)
        quizzes_path = OUTPUT_DIR / "quizzes_and_progress.png"
        page.screenshot(path=str(quizzes_path), full_page=False)
        print(f"Captured: {quizzes_path}")

        # 6. MongoDB Analytics
        page.click(".sidebar-menu a[data-view='analytics']")
        page.wait_for_selector("#agg1-table-body tr")
        time.sleep(0.5)
        analytics_path = OUTPUT_DIR / "mongodb_analytics.png"
        page.screenshot(path=str(analytics_path), full_page=False)
        print(f"Captured: {analytics_path}")

        # 7. Neo4j Graph Insights
        page.click(".sidebar-menu a[data-view='graph']")
        page.wait_for_selector("#prereq-course-select")
        # Trigger prerequisite explorer to show live graph results
        page.click("#btn-explore-prereqs")
        page.wait_for_selector("#prereq-results div")
        time.sleep(0.5)
        graph_path = OUTPUT_DIR / "neo4j_graph.png"
        page.screenshot(path=str(graph_path), full_page=False)
        print(f"Captured: {graph_path}")

        context.close()

        # 8. Mobile Viewport (375x667)
        mobile_context = browser.new_context(
            viewport={"width": 375, "height": 667},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        )
        mobile_page = mobile_context.new_page()
        mobile_page.goto(BASE_URL, wait_until="networkidle")
        mobile_page.wait_for_selector("#kpi-students:not(:empty)")
        time.sleep(1)
        mobile_path = OUTPUT_DIR / "mobile_layout.png"
        mobile_page.screenshot(path=str(mobile_path), full_page=False)
        print(f"Captured: {mobile_path}")

        mobile_context.close()
        browser.close()

    print("All screenshots successfully captured!")

if __name__ == "__main__":
    capture_portal_screenshots()
