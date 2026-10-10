/**
 * Quizzes & Progress View Logic
 */

async function loadQuizzes() {
    const courseId = document.getElementById("quizzes-course-filter")?.value || "";
    const url = courseId ? `/api/quizzes?course_id=${encodeURIComponent(courseId)}` : "/api/quizzes";

    const tbody = document.getElementById("quizzes-table-body");
    tbody.innerHTML = `<tr><td colspan="7" class="text-center">Loading quizzes...</td></tr>`;

    try {
        const quizzes = await fetchApi(url);
        if (quizzes.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No quizzes configured.</td></tr>`;
            return;
        }

        tbody.innerHTML = quizzes.map(q => {
            const questionPreview = (q.questions || []).map((quest, idx) => `
                <div class="mb-1" style="font-size: 11px;">
                    <strong>Q${idx + 1}:</strong> ${escapeHtml(quest.question_text || '')} (${quest.points || 5} pts)
                </div>
            `).join("");

            return `
                <tr>
                    <td><strong>${escapeHtml(q.quiz_id)}</strong></td>
                    <td><span class="badge badge-primary">${escapeHtml(q.course_id)}</span> <small>${escapeHtml(q.course_title || '')}</small></td>
                    <td><strong>${escapeHtml(q.title)}</strong></td>
                    <td><span class="badge badge-info">${q.total_points || 10} pts</span></td>
                    <td>${q.time_limit_minutes || 15} mins</td>
                    <td>
                        <details style="cursor: pointer;">
                            <summary style="font-weight: 600; color: var(--primary);">View ${q.question_count || 0} Questions</summary>
                            <div class="mt-2 results-box" style="padding: 8px;">${questionPreview}</div>
                        </details>
                    </td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="deleteQuizAction('${escapeHtml(q.quiz_id)}')">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Error: ${escapeHtml(err.message)}</td></tr>`;
        showToast(err.message, "error");
    }
}

async function loadProgressRecords() {
    const statusFilter = document.getElementById("progress-status-filter")?.value || "";
    const url = statusFilter ? `/api/quizzes/progress/all?status=${encodeURIComponent(statusFilter)}` : "/api/quizzes/progress/all";

    const tbody = document.getElementById("progress-table-body");
    tbody.innerHTML = `<tr><td colspan="7" class="text-center">Loading progress records...</td></tr>`;

    try {
        const records = await fetchApi(url);
        if (records.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No progress records found.</td></tr>`;
            return;
        }

        tbody.innerHTML = records.map(p => {
            const badgeClass = p.status === "completed" ? "badge-success" : (p.status === "in_progress" ? "badge-info" : "badge-warning");
            const scoresCount = (p.quiz_scores || []).length;
            const lastAccessed = p.last_accessed ? new Date(p.last_accessed).toLocaleDateString() : "N/A";

            return `
                <tr>
                    <td><strong>${escapeHtml(p.student_name || p.student_id)}</strong> <small class="text-muted">(${escapeHtml(p.student_id)})</small></td>
                    <td><span class="badge badge-primary">${escapeHtml(p.course_id)}</span> ${escapeHtml(p.course_title || '')}</td>
                    <td style="min-width: 140px;">
                        <div class="d-flex align-items-center gap-2">
                            <div class="progress-bar-container">
                                <div class="progress-bar-fill ${p.status === 'completed' ? 'completed' : ''}" style="width: ${p.completion_percentage}%;"></div>
                            </div>
                            <span style="font-size: 11px; font-weight: 600;">${p.completion_percentage}%</span>
                        </div>
                    </td>
                    <td><span class="badge ${badgeClass}">${escapeHtml(p.status)}</span></td>
                    <td><span class="badge badge-primary">${scoresCount} attempt(s)</span></td>
                    <td><span class="text-muted" style="font-size: 12px;">${lastAccessed}</span></td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="openUpdateProgressModal('${escapeHtml(p.student_id)}', '${escapeHtml(p.course_id)}', ${p.completion_percentage}, '${escapeHtml(p.status)}')">
                            <i class="fa-solid fa-sliders"></i> Adjust
                        </button>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Error: ${escapeHtml(err.message)}</td></tr>`;
        showToast(err.message, "error");
    }
}

async function deleteQuizAction(quizId) {
    if (!confirm(`Are you sure you want to delete quiz ${quizId}?`)) return;

    try {
        const res = await fetchApi(`/api/quizzes/${encodeURIComponent(quizId)}`, { method: "DELETE" });
        showToast(res.message, "success");
        loadQuizzes();
    } catch (err) {
        showToast(err.message, "error");
    }
}

function openUpdateProgressModal(studentId, courseId, pct, status) {
    document.getElementById("prog-student-id").value = studentId;
    document.getElementById("prog-course-id").value = courseId;
    document.getElementById("prog-target-label").textContent = `${studentId} in course ${courseId}`;
    document.getElementById("prog-pct").value = pct;
    document.getElementById("prog-pct-label").textContent = `${pct}%`;
    document.getElementById("prog-status").value = status;
    openModal("modal-progress");
}

document.addEventListener("DOMContentLoaded", () => {
    // Quizzes filter
    const qCourseFilter = document.getElementById("quizzes-course-filter");
    if (qCourseFilter) qCourseFilter.addEventListener("change", loadQuizzes);

    // Progress filter
    const pStatusFilter = document.getElementById("progress-status-filter");
    if (pStatusFilter) pStatusFilter.addEventListener("change", loadProgressRecords);

    // Slider label updates
    const progSlider = document.getElementById("prog-pct");
    if (progSlider) {
        progSlider.addEventListener("input", (e) => {
            const val = e.target.value;
            document.getElementById("prog-pct-label").textContent = `${val}%`;
            if (parseInt(val) === 100) {
                document.getElementById("prog-status").value = "completed";
            }
        });
    }

    // Form progress update
    const formProg = document.getElementById("form-progress");
    if (formProg) {
        formProg.addEventListener("submit", async (e) => {
            e.preventDefault();
            const sid = document.getElementById("prog-student-id").value;
            const cid = document.getElementById("prog-course-id").value;
            const completion_percentage = parseFloat(document.getElementById("prog-pct").value);
            const status = document.getElementById("prog-status").value;

            try {
                const res = await fetchApi(`/api/quizzes/progress/${encodeURIComponent(sid)}/${encodeURIComponent(cid)}`, {
                    method: "PUT",
                    body: JSON.stringify({ completion_percentage, status })
                });
                showToast(res.message, "success");
                closeModal("modal-progress");
                loadProgressRecords();
                loadDashboard();
            } catch (err) {
                showToast(err.message, "error");
            }
        });
    }

    // Add quiz modal handling
    const addQuizBtn = document.getElementById("btn-add-quiz");
    if (addQuizBtn) {
        addQuizBtn.addEventListener("click", () => {
            document.getElementById("qz-id").value = "";
            document.getElementById("qz-course-id").value = "C001";
            document.getElementById("qz-title").value = "";
            document.getElementById("qz-points").value = "20";
            document.getElementById("qz-time").value = "20";
            document.getElementById("qz-q1-text").value = "";
            document.getElementById("qz-q1-answer").value = "";
            openModal("modal-quiz");
        });
    }

    const formQuiz = document.getElementById("form-quiz");
    if (formQuiz) {
        formQuiz.addEventListener("submit", async (e) => {
            e.preventDefault();
            const qid = document.getElementById("qz-id").value.trim();
            const cid = document.getElementById("qz-course-id").value.trim();
            const title = document.getElementById("qz-title").value.trim();
            const points = parseInt(document.getElementById("qz-points").value);
            const timeLimit = parseInt(document.getElementById("qz-time").value);
            const q1Text = document.getElementById("qz-q1-text").value.trim();
            const q1Ans = document.getElementById("qz-q1-answer").value.trim();

            try {
                const res = await fetchApi("/api/quizzes", {
                    method: "POST",
                    body: JSON.stringify({
                        quiz_id: qid,
                        course_id: cid,
                        title: title,
                        total_points: points,
                        time_limit_minutes: timeLimit,
                        questions: [
                            {
                                question_id: `${qid}_1`,
                                question_text: q1Text,
                                options: [q1Ans, "Alternative Option B", "Alternative Option C"],
                                correct_answer: q1Ans,
                                points: points
                            }
                        ]
                    })
                });
                showToast(res.message, "success");
                closeModal("modal-quiz");
                loadQuizzes();
            } catch (err) {
                showToast(err.message, "error");
            }
        });
    }
});
