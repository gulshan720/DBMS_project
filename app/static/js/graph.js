/**
 * Graph Insights View Logic (Neo4j Traversals & Cypher Analytics)
 */

let graphSelectsInitialized = false;

async function initGraphSelects() {
    if (graphSelectsInitialized) return;
    try {
        const [courses, students] = await Promise.all([
            fetchApi("/api/courses"),
            fetchApi("/api/students")
        ]);

        const prereqSelect = document.getElementById("prereq-course-select");
        if (prereqSelect && courses.length > 0) {
            prereqSelect.innerHTML = courses.map(c => 
                `<option value="${escapeHtml(c.course_id)}" ${c.course_id === 'C004' ? 'selected' : ''}>[${escapeHtml(c.course_id)}] ${escapeHtml(c.title)}</option>`
            ).join("");
        }

        const recSelect = document.getElementById("rec-student-select");
        const gapSelect = document.getElementById("gap-student-select");
        if (students.length > 0) {
            const studentOptions = students.map((s, idx) => 
                `<option value="${escapeHtml(s.student_id)}" ${idx === 0 ? 'selected' : ''}>[${escapeHtml(s.student_id)}] ${escapeHtml(s.name)}</option>`
            ).join("");
            if (recSelect) recSelect.innerHTML = studentOptions;
            if (gapSelect) gapSelect.innerHTML = studentOptions;
        }

        graphSelectsInitialized = true;
    } catch (err) {
        console.warn("Failed to dynamically populate graph select options:", err);
    }
}

async function loadGraphInsights() {
    initGraphSelects();
    loadCoursePopularity();
    loadInstructorWorkload();
}

async function explorePrerequisites() {
    const courseId = document.getElementById("prereq-course-select")?.value || "C004";
    const container = document.getElementById("prereq-results");
    container.innerHTML = `<p class="text-center">Traversing prerequisite graph...</p>`;

    try {
        const data = await fetchApi(`/api/graph/prerequisites/${encodeURIComponent(courseId)}`);
        const prereqs = data.prerequisites || [];

        if (prereqs.length === 0) {
            container.innerHTML = `<div class="badge badge-success mb-2">Foundational Course</div><p>No prerequisites required for <strong>${escapeHtml(courseId)}</strong>.</p>`;
            return;
        }

        container.innerHTML = `
            <h5 class="mb-2">Prerequisite Chain for <code>${escapeHtml(courseId)}</code> (${prereqs.length} dependency levels):</h5>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                ${prereqs.map(p => `
                    <div style="background: white; border-left: 4px solid var(--primary); padding: 8px 12px; border-radius: 4px; box-shadow: var(--shadow-sm); display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>[${escapeHtml(p.prerequisite_id)}]</strong> ${escapeHtml(p.prerequisite_title)}
                        </div>
                        <span class="badge badge-primary">Depth ${p.depth}</span>
                    </div>
                `).join("")}
            </div>
        `;
    } catch (err) {
        container.innerHTML = `<p class="text-danger">Failed to traverse prerequisites: ${escapeHtml(err.message)}</p>`;
    }
}

async function findLearningPath() {
    const start = document.getElementById("path-start")?.value.trim() || "C001";
    const end = document.getElementById("path-end")?.value.trim() || "C004";
    const container = document.getElementById("path-results");
    container.innerHTML = `<p class="text-center">Finding shortest prerequisite path...</p>`;

    try {
        const data = await fetchApi(`/api/graph/learning-path?start_course_id=${encodeURIComponent(start)}&end_course_id=${encodeURIComponent(end)}`);
        const path = data.path || [];

        if (path.length === 0) {
            container.innerHTML = `<p class="text-warning"><i class="fa-solid fa-circle-exclamation"></i> No direct or transitive prerequisite path connects <strong>${escapeHtml(start)}</strong> to <strong>${escapeHtml(end)}</strong>.</p>`;
            return;
        }

        container.innerHTML = `
            <h5 class="mb-2"><i class="fa-solid fa-graduation-cap"></i> Optimal Learning Path (${data.step_count} courses):</h5>
            <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 8px;">
                ${path.map((node, idx) => `
                    <div style="background: white; border: 1px solid var(--border-color); padding: 8px 14px; border-radius: 8px; font-weight: 600;">
                        <span class="badge badge-primary" style="margin-right: 4px;">${escapeHtml(node.course_id)}</span>
                        ${escapeHtml(node.title)}
                    </div>
                    ${idx < path.length - 1 ? '<i class="fa-solid fa-arrow-right" style="color: var(--primary);"></i>' : ''}
                `).join("")}
            </div>
        `;
    } catch (err) {
        container.innerHTML = `<p class="text-danger">Error: ${escapeHtml(err.message)}</p>`;
    }
}

async function getRecommendations() {
    const studentId = document.getElementById("rec-student-select")?.value || "S001";
    const container = document.getElementById("rec-results");
    container.innerHTML = `<p class="text-center">Querying collaborative filtering graph...</p>`;

    try {
        const data = await fetchApi(`/api/graph/recommendations/${encodeURIComponent(studentId)}`);
        const recs = data.recommendations || [];

        if (recs.length === 0) {
            container.innerHTML = `<p class="text-muted">No personalized recommendations found for ${escapeHtml(studentId)} (student may already be enrolled in all peer courses).</p>`;
            return;
        }

        container.innerHTML = `
            <h5 class="mb-2">Recommended Courses for <code>${escapeHtml(studentId)}</code>:</h5>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                ${recs.map(r => `
                    <div style="background: white; border: 1px solid var(--border-color); padding: 10px 14px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>[${escapeHtml(r.course_id)}] ${escapeHtml(r.title)}</strong>
                            <div style="font-size: 11px; color: var(--text-secondary);">Category: ${escapeHtml(r.category || 'N/A')}</div>
                        </div>
                        <span class="badge badge-info">${r.similar_student_count || 1} peer student(s) also enrolled</span>
                    </div>
                `).join("")}
            </div>
        `;
    } catch (err) {
        container.innerHTML = `<p class="text-danger">Error: ${escapeHtml(err.message)}</p>`;
    }
}

async function checkSkillGaps() {
    const studentId = document.getElementById("gap-student-select")?.value || "S001";
    const container = document.getElementById("gap-results");
    container.innerHTML = `<p class="text-center">Analyzing prerequisite skill gaps...</p>`;

    try {
        const data = await fetchApi(`/api/graph/analytics/skill-gap/${encodeURIComponent(studentId)}`);
        const gaps = data.skill_gaps || [];

        if (gaps.length === 0) {
            container.innerHTML = `<div class="badge badge-success mb-2"><i class="fa-solid fa-check"></i> All Skills Satisfied</div><p>Student has all required skills for enrolled courses.</p>`;
            return;
        }

        container.innerHTML = `
            <h5 class="mb-2" style="color: #b45309;">Missing Prerequisites for <code>${escapeHtml(studentId)}</code>:</h5>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                ${gaps.map(g => `
                    <div style="background: #fffbeb; border: 1px solid #fde68a; padding: 10px 14px; border-radius: 8px;">
                        <strong style="color: #92400e;">⚠ Missing Skill: ${escapeHtml(g.skill_name)} (ID: ${escapeHtml(g.skill_id)})</strong>
                        <div style="font-size: 12px; color: #78350f; margin-top: 2px;">
                            Required by: ${(g.required_by_courses || []).map(c => `<code>${escapeHtml(c)}</code>`).join(", ")}
                        </div>
                    </div>
                `).join("")}
            </div>
        `;
    } catch (err) {
        container.innerHTML = `<p class="text-danger">Error: ${escapeHtml(err.message)}</p>`;
    }
}

async function loadCoursePopularity() {
    const tbody = document.getElementById("neo-pop-table");
    if (!tbody) return;
    try {
        const data = await fetchApi("/api/graph/analytics/popularity");
        tbody.innerHTML = data.map(item => `
            <tr>
                <td><strong>[${escapeHtml(item.course_id)}]</strong> ${escapeHtml(item.title)}</td>
                <td><span class="badge badge-info">${item.enrolled_count}</span></td>
                <td><span class="badge badge-success">${item.completed_count}</span></td>
                <td><strong>${item.total_students}</strong></td>
            </tr>
        `).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-danger">Failed to load: ${escapeHtml(err.message)}</td></tr>`;
    }
}

async function loadInstructorWorkload() {
    const tbody = document.getElementById("neo-workload-table");
    if (!tbody) return;
    try {
        const data = await fetchApi("/api/graph/analytics/instructor-workload");
        tbody.innerHTML = data.map(item => `
            <tr>
                <td><strong>${escapeHtml(item.name)}</strong> <small>(${escapeHtml(item.instructor_id)})</small></td>
                <td><span class="badge badge-warning">★ ${item.rating || 'N/A'}</span></td>
                <td>${(item.courses_taught || []).length} course(s)</td>
                <td><span class="badge badge-primary">${item.student_count || 0} students</span></td>
            </tr>
        `).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-danger">Failed to load: ${escapeHtml(err.message)}</td></tr>`;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("btn-explore-prereqs")?.addEventListener("click", explorePrerequisites);
    document.getElementById("btn-find-path")?.addEventListener("click", findLearningPath);
    document.getElementById("btn-get-recs")?.addEventListener("click", getRecommendations);
    document.getElementById("btn-check-gaps")?.addEventListener("click", checkSkillGaps);
});
