/**
 * Students Management View Logic
 */

let editingStudentId = null;

async function loadStudents() {
    const searchInput = document.getElementById("students-search");
    const query = searchInput ? searchInput.value.trim() : "";
    const url = query ? `/api/students?search=${encodeURIComponent(query)}` : "/api/students";

    const tbody = document.getElementById("students-table-body");
    tbody.innerHTML = `<tr><td colspan="6" class="text-center">Loading students...</td></tr>`;

    try {
        const students = await fetchApi(url);
        if (students.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No students found.</td></tr>`;
            return;
        }

        tbody.innerHTML = students.map(s => {
            const enrolledList = (s.courses_enrolled && s.courses_enrolled.length > 0)
                ? s.courses_enrolled.map(c => `<span class="badge badge-primary">${escapeHtml(c)}</span>`).join(" ")
                : `<span class="text-muted">None</span>`;

            return `
                <tr>
                    <td><strong>${escapeHtml(s.student_id)}</strong></td>
                    <td>${escapeHtml(s.name)}</td>
                    <td>${escapeHtml(s.email)}</td>
                    <td>${escapeHtml(s.phone || "—")}</td>
                    <td>${enrolledList}</td>
                    <td>
                        <div class="d-flex gap-1">
                            <button class="btn btn-secondary btn-sm" onclick="viewStudentDetails('${escapeHtml(s.student_id)}')">
                                <i class="fa-solid fa-eye"></i> Details
                            </button>
                            <button class="btn btn-outline btn-sm" onclick="editStudentModal('${escapeHtml(s.student_id)}', '${escapeHtml(s.name)}', '${escapeHtml(s.email)}', '${escapeHtml(s.phone || '')}')">
                                <i class="fa-solid fa-pen"></i>
                            </button>
                            <button class="btn btn-danger btn-sm" onclick="deleteStudentAction('${escapeHtml(s.student_id)}')">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error: ${escapeHtml(err.message)}</td></tr>`;
        showToast(err.message, "error");
    }
}

async function viewStudentDetails(studentId) {
    const modalBody = document.getElementById("student-details-body");
    modalBody.innerHTML = `<p class="text-center">Loading student details...</p>`;
    openModal("modal-student-details");

    try {
        const data = await fetchApi(`/api/students/${encodeURIComponent(studentId)}`);
        const s = data.student;

        // Progress List
        let progressHtml = `<p class="text-muted">No active course enrollments.</p>`;
        if (data.progress && data.progress.length > 0) {
            progressHtml = data.progress.map(p => `
                <div class="stat-pill mb-2" style="text-align: left;">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <strong>${escapeHtml(p.course_id)}</strong>
                        <span class="badge ${p.status === 'completed' ? 'badge-success' : 'badge-info'}">${escapeHtml(p.status)}</span>
                    </div>
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill ${p.status === 'completed' ? 'completed' : ''}" style="width: ${p.completion_percentage}%;"></div>
                    </div>
                    <div class="d-flex justify-content-between mt-1" style="font-size: 11px;">
                        <span>Completion: ${p.completion_percentage}%</span>
                        <span class="text-muted">Attempts: ${(p.quiz_scores || []).length}</span>
                    </div>
                </div>
            `).join("");
        }

        // Skills List from Neo4j
        let skillsHtml = `<p class="text-muted">No verified skills recorded in graph.</p>`;
        if (data.skills && data.skills.length > 0) {
            skillsHtml = data.skills.map(sk => `
                <span class="badge badge-success mb-1" style="margin-right: 4px;">
                    ${escapeHtml(sk.name)} (${escapeHtml(sk.proficiency || 'General')})
                </span>
            `).join("");
        }

        modalBody.innerHTML = `
            <div class="student-profile-card mb-3">
                <h4>${escapeHtml(s.name)} <span class="badge badge-primary">${escapeHtml(s.student_id)}</span></h4>
                <p class="text-muted mb-2"><i class="fa-solid fa-envelope"></i> ${escapeHtml(s.email)} | <i class="fa-solid fa-phone"></i> ${escapeHtml(s.phone || 'N/A')}</p>
            </div>
            
            <div class="row" style="display: flex; gap: 20px;">
                <div style="flex: 1;">
                    <h5 class="mb-2"><i class="fa-solid fa-bars-progress"></i> Course Progress (MongoDB)</h5>
                    ${progressHtml}
                </div>
                <div style="flex: 1;">
                    <h5 class="mb-2"><i class="fa-solid fa-award"></i> Skills Acquired (Neo4j Graph)</h5>
                    <div class="mb-3">${skillsHtml}</div>

                    <h5 class="mb-2"><i class="fa-solid fa-plus"></i> Enroll in New Course</h5>
                    <div class="input-inline">
                        <input type="text" id="quick-enroll-cid" class="form-input" placeholder="Course ID (e.g. C005)">
                        <button class="btn btn-primary btn-sm" onclick="enrollStudentAction('${escapeHtml(s.student_id)}')">Enroll</button>
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        modalBody.innerHTML = `<p class="text-danger">Failed to load details: ${escapeHtml(err.message)}</p>`;
    }
}

async function enrollStudentAction(studentId) {
    const input = document.getElementById("quick-enroll-cid");
    const courseId = input ? input.value.trim() : "";
    if (!courseId) {
        showToast("Please enter a valid Course ID", "warning");
        return;
    }

    try {
        const res = await fetchApi(`/api/students/${encodeURIComponent(studentId)}/enroll`, {
            method: "POST",
            body: JSON.stringify({ course_id: courseId })
        });
        showToast(res.message, "success");
        viewStudentDetails(studentId);
        loadStudents();
    } catch (err) {
        showToast(err.message, "error");
    }
}

function openAddStudentModal() {
    editingStudentId = null;
    document.getElementById("modal-student-title").textContent = "Register Student";
    document.getElementById("std-id").value = "";
    document.getElementById("std-id").disabled = false;
    document.getElementById("std-name").value = "";
    document.getElementById("std-email").value = "";
    document.getElementById("std-phone").value = "";
    openModal("modal-student");
}

function editStudentModal(studentId, name, email, phone) {
    editingStudentId = studentId;
    document.getElementById("modal-student-title").textContent = `Edit Student (${studentId})`;
    document.getElementById("std-id").value = studentId;
    document.getElementById("std-id").disabled = true;
    document.getElementById("std-name").value = name;
    document.getElementById("std-email").value = email;
    document.getElementById("std-phone").value = phone;
    openModal("modal-student");
}

async function deleteStudentAction(studentId) {
    if (!confirm(`Are you sure you want to delete student ${studentId}? This will remove associated progress and graph relationships.`)) {
        return;
    }

    try {
        const res = await fetchApi(`/api/students/${encodeURIComponent(studentId)}`, {
            method: "DELETE"
        });
        showToast(res.message, "success");
        loadStudents();
    } catch (err) {
        showToast(err.message, "error");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("students-search");
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener("input", () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(loadStudents, 300);
        });
    }

    const addBtn = document.getElementById("btn-add-student");
    if (addBtn) addBtn.addEventListener("click", openAddStudentModal);

    const form = document.getElementById("form-student");
    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const sid = document.getElementById("std-id").value.trim();
            const name = document.getElementById("std-name").value.trim();
            const email = document.getElementById("std-email").value.trim();
            const phone = document.getElementById("std-phone").value.trim();

            try {
                if (editingStudentId) {
                    const res = await fetchApi(`/api/students/${encodeURIComponent(editingStudentId)}`, {
                        method: "PUT",
                        body: JSON.stringify({ name, email, phone })
                    });
                    showToast(res.message, "success");
                } else {
                    const res = await fetchApi("/api/students", {
                        method: "POST",
                        body: JSON.stringify({ student_id: sid, name, email, phone })
                    });
                    showToast(res.message, "success");
                }
                closeModal("modal-student");
                loadStudents();
            } catch (err) {
                showToast(err.message, "error");
            }
        });
    }
});
