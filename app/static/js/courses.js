/**
 * Courses Management View Logic
 */

let editingCourseId = null;

async function initCourseFilters() {
    try {
        const meta = await fetchApi("/api/courses/meta");
        const catSelect = document.getElementById("course-category-filter");
        if (catSelect && meta.categories) {
            catSelect.innerHTML = `<option value="">All Categories</option>` +
                meta.categories.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");
        }
    } catch (err) {
        console.error("Failed to load course metadata:", err);
    }
}

async function loadCourses() {
    const search = document.getElementById("courses-search")?.value.trim() || "";
    const category = document.getElementById("course-category-filter")?.value || "";
    const difficulty = document.getElementById("course-difficulty-filter")?.value || "";

    const params = new URLSearchParams();
    if (search) params.append("search", search);
    if (category) params.append("category", category);
    if (difficulty) params.append("difficulty", difficulty);

    const url = `/api/courses?${params.toString()}`;
    const tbody = document.getElementById("courses-table-body");
    tbody.innerHTML = `<tr><td colspan="8" class="text-center">Loading courses...</td></tr>`;

    try {
        const courses = await fetchApi(url);
        if (courses.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No courses found matching filters.</td></tr>`;
            return;
        }

        tbody.innerHTML = courses.map(c => {
            let diffBadge = "badge-info";
            if (c.difficulty_level === "Beginner") diffBadge = "badge-success";
            else if (c.difficulty_level === "Advanced") diffBadge = "badge-danger";
            else if (c.difficulty_level === "Intermediate") diffBadge = "badge-warning";

            return `
                <tr>
                    <td><strong>${escapeHtml(c.course_id)}</strong></td>
                    <td>${escapeHtml(c.title)}</td>
                    <td><span class="badge badge-primary">${escapeHtml(c.category)}</span></td>
                    <td><span class="badge ${diffBadge}">${escapeHtml(c.difficulty_level)}</span></td>
                    <td>${c.duration_hours || 0} hrs</td>
                    <td>₹${(c.price || 0).toLocaleString()}</td>
                    <td>${escapeHtml(c.instructor_name || c.instructor_id || 'N/A')}</td>
                    <td>
                        <div class="d-flex gap-1">
                            <button class="btn btn-secondary btn-sm" onclick="viewCourseDetails('${escapeHtml(c.course_id)}')">
                                <i class="fa-solid fa-circle-info"></i>
                            </button>
                            <button class="btn btn-outline btn-sm" onclick="editCourseModal('${escapeHtml(c.course_id)}', '${escapeHtml(c.title)}', '${escapeHtml(c.category)}', '${escapeHtml(c.difficulty_level)}', '${escapeHtml(c.instructor_id)}', ${c.duration_hours || 40}, ${c.price || 0})">
                                <i class="fa-solid fa-pen"></i>
                            </button>
                            <button class="btn btn-danger btn-sm" onclick="deleteCourseAction('${escapeHtml(c.course_id)}')">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Error: ${escapeHtml(err.message)}</td></tr>`;
        showToast(err.message, "error");
    }
}

async function viewCourseDetails(courseId) {
    try {
        const data = await fetchApi(`/api/courses/${encodeURIComponent(courseId)}`);
        const c = data.course;
        const prereqs = data.prerequisites || [];
        const materials = data.materials || [];
        const quizzes = data.quizzes || [];

        const prereqText = prereqs.length > 0
            ? prereqs.map(p => `Depth ${p.depth}: [${escapeHtml(p.prerequisite_id)}] ${escapeHtml(p.prerequisite_title)}`).join("<br>")
            : "No prerequisites required (Foundational Course)";

        const materialsText = materials.length > 0
            ? materials.map(m => `• [${escapeHtml(m.type.toUpperCase())}] ${escapeHtml(m.title)} (${m.duration_minutes || 15}m)`).join("<br>")
            : "No materials uploaded.";

        const quizzesText = quizzes.length > 0
            ? quizzes.map(q => `• ${escapeHtml(q.title)} (${q.total_points} points, ${(q.questions || []).length} questions)`).join("<br>")
            : "No quizzes configured.";

        alert(`Course Details: [${c.course_id}] ${c.title}\n\nCategory: ${c.category}\nDifficulty: ${c.difficulty_level}\nDuration: ${c.duration_hours}h | Price: ₹${c.price}\n\nPrerequisites (Neo4j Graph):\n${prereqs.map(p => `• [${p.prerequisite_id}] ${p.prerequisite_title}`).join("\n") || "None"}\n\nCurriculum (MongoDB):\nMaterials: ${materials.length} item(s)\nQuizzes: ${quizzes.length} quiz(zes)`);
    } catch (err) {
        showToast(err.message, "error");
    }
}

function openAddCourseModal() {
    editingCourseId = null;
    document.getElementById("modal-course-title").textContent = "Add Course";
    document.getElementById("crs-id").value = "";
    document.getElementById("crs-id").disabled = false;
    document.getElementById("crs-title").value = "";
    document.getElementById("crs-category").value = "Programming";
    document.getElementById("crs-difficulty").value = "Beginner";
    document.getElementById("crs-instructor").value = "I001";
    document.getElementById("crs-duration").value = "40";
    document.getElementById("crs-price").value = "2999";
    openModal("modal-course");
}

function editCourseModal(courseId, title, category, difficulty, instructorId, duration, price) {
    editingCourseId = courseId;
    document.getElementById("modal-course-title").textContent = `Edit Course (${courseId})`;
    document.getElementById("crs-id").value = courseId;
    document.getElementById("crs-id").disabled = true;
    document.getElementById("crs-title").value = title;
    document.getElementById("crs-category").value = category;
    document.getElementById("crs-difficulty").value = difficulty;
    document.getElementById("crs-instructor").value = instructorId;
    document.getElementById("crs-duration").value = duration;
    document.getElementById("crs-price").value = price;
    openModal("modal-course");
}

async function deleteCourseAction(courseId) {
    if (!confirm(`Are you sure you want to delete course ${courseId}? This will remove associated materials and quizzes.`)) {
        return;
    }

    try {
        const res = await fetchApi(`/api/courses/${encodeURIComponent(courseId)}`, {
            method: "DELETE"
        });
        showToast(res.message, "success");
        loadCourses();
    } catch (err) {
        showToast(err.message, "error");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initCourseFilters();

    const searchInput = document.getElementById("courses-search");
    if (searchInput) {
        let timer;
        searchInput.addEventListener("input", () => {
            clearTimeout(timer);
            timer = setTimeout(loadCourses, 300);
        });
    }

    const catFilter = document.getElementById("course-category-filter");
    if (catFilter) catFilter.addEventListener("change", loadCourses);

    const diffFilter = document.getElementById("course-difficulty-filter");
    if (diffFilter) diffFilter.addEventListener("change", loadCourses);

    const addBtn = document.getElementById("btn-add-course");
    if (addBtn) addBtn.addEventListener("click", openAddCourseModal);

    const form = document.getElementById("form-course");
    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const cid = document.getElementById("crs-id").value.trim();
            const title = document.getElementById("crs-title").value.trim();
            const category = document.getElementById("crs-category").value.trim();
            const difficulty_level = document.getElementById("crs-difficulty").value;
            const instructor_id = document.getElementById("crs-instructor").value.trim();
            const duration_hours = parseInt(document.getElementById("crs-duration").value);
            const price = parseFloat(document.getElementById("crs-price").value);

            try {
                if (editingCourseId) {
                    const res = await fetchApi(`/api/courses/${encodeURIComponent(editingCourseId)}`, {
                        method: "PUT",
                        body: JSON.stringify({ title, category, difficulty_level, instructor_id, duration_hours, price })
                    });
                    showToast(res.message, "success");
                } else {
                    const res = await fetchApi("/api/courses", {
                        method: "POST",
                        body: JSON.stringify({ course_id: cid, title, category, difficulty_level, instructor_id, duration_hours, price })
                    });
                    showToast(res.message, "success");
                }
                closeModal("modal-course");
                loadCourses();
            } catch (err) {
                showToast(err.message, "error");
            }
        });
    }
});
