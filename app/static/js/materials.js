/**
 * Learning Materials View Logic
 */

let editingMaterialId = null;

async function initMaterialsFilters() {
    try {
        const courses = await fetchApi("/api/courses");
        const select = document.getElementById("materials-course-filter");
        if (select) {
            select.innerHTML = `<option value="">All Courses</option>` +
                courses.map(c => `<option value="${escapeHtml(c.course_id)}">[${escapeHtml(c.course_id)}] ${escapeHtml(c.title)}</option>`).join("");
        }
    } catch (err) {
        console.error("Failed to load course filter for materials:", err);
    }
}

async function loadMaterials() {
    const courseId = document.getElementById("materials-course-filter")?.value || "";
    const type = document.getElementById("materials-type-filter")?.value || "";

    const params = new URLSearchParams();
    if (courseId) params.append("course_id", courseId);
    if (type) params.append("type", type);

    const tbody = document.getElementById("materials-table-body");
    tbody.innerHTML = `<tr><td colspan="7" class="text-center">Loading materials...</td></tr>`;

    try {
        const materials = await fetchApi(`/api/materials?${params.toString()}`);
        if (materials.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No learning materials found.</td></tr>`;
            return;
        }

        tbody.innerHTML = materials.map(m => {
            let typeBadge = "badge-info";
            let typeIcon = "fa-file-lines";
            if (m.type === "video") { typeBadge = "badge-rose"; typeIcon = "fa-video"; }
            else if (m.type === "pdf") { typeBadge = "badge-warning"; typeIcon = "fa-file-pdf"; }

            return `
                <tr>
                    <td><strong>${escapeHtml(m.material_id)}</strong></td>
                    <td><span class="badge badge-primary">${escapeHtml(m.course_id)}</span> <small>${escapeHtml(m.course_title || '')}</small></td>
                    <td>${escapeHtml(m.title)}</td>
                    <td><span class="badge ${typeBadge}"><i class="fa-solid ${typeIcon}"></i> ${escapeHtml(m.type)}</span></td>
                    <td>${m.duration_minutes || 15} mins</td>
                    <td><a href="${escapeHtml(m.content_url)}" target="_blank" class="text-muted" style="text-decoration: underline;"><i class="fa-solid fa-arrow-up-right-from-square"></i> Resource</a></td>
                    <td>
                        <div class="d-flex gap-1">
                            <button class="btn btn-outline btn-sm" onclick="editMaterialModal('${escapeHtml(m.material_id)}', '${escapeHtml(m.course_id)}', '${escapeHtml(m.title)}', '${escapeHtml(m.type)}', '${escapeHtml(m.content_url)}', ${m.duration_minutes || 20})">
                                <i class="fa-solid fa-pen"></i>
                            </button>
                            <button class="btn btn-danger btn-sm" onclick="deleteMaterialAction('${escapeHtml(m.material_id)}')">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Error: ${escapeHtml(err.message)}</td></tr>`;
        showToast(err.message, "error");
    }
}

function openAddMaterialModal() {
    editingMaterialId = null;
    document.getElementById("modal-material-title").textContent = "Add Learning Material";
    document.getElementById("mat-id").value = "";
    document.getElementById("mat-id").disabled = false;
    document.getElementById("mat-course-id").value = "C001";
    document.getElementById("mat-title").value = "";
    document.getElementById("mat-type").value = "video";
    document.getElementById("mat-url").value = "https://example.com/material";
    document.getElementById("mat-duration").value = "20";
    openModal("modal-material");
}

function editMaterialModal(id, courseId, title, type, url, duration) {
    editingMaterialId = id;
    document.getElementById("modal-material-title").textContent = `Edit Material (${id})`;
    document.getElementById("mat-id").value = id;
    document.getElementById("mat-id").disabled = true;
    document.getElementById("mat-course-id").value = courseId;
    document.getElementById("mat-title").value = title;
    document.getElementById("mat-type").value = type;
    document.getElementById("mat-url").value = url;
    document.getElementById("mat-duration").value = duration;
    openModal("modal-material");
}

async function deleteMaterialAction(id) {
    if (!confirm(`Are you sure you want to delete material ${id}?`)) return;

    try {
        const res = await fetchApi(`/api/materials/${encodeURIComponent(id)}`, { method: "DELETE" });
        showToast(res.message, "success");
        loadMaterials();
    } catch (err) {
        showToast(err.message, "error");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initMaterialsFilters();

    const courseFilter = document.getElementById("materials-course-filter");
    if (courseFilter) courseFilter.addEventListener("change", loadMaterials);

    const typeFilter = document.getElementById("materials-type-filter");
    if (typeFilter) typeFilter.addEventListener("change", loadMaterials);

    const addBtn = document.getElementById("btn-add-material");
    if (addBtn) addBtn.addEventListener("click", openAddMaterialModal);

    const form = document.getElementById("form-material");
    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const material_id = document.getElementById("mat-id").value.trim();
            const course_id = document.getElementById("mat-course-id").value.trim();
            const title = document.getElementById("mat-title").value.trim();
            const type = document.getElementById("mat-type").value;
            const content_url = document.getElementById("mat-url").value.trim();
            const duration_minutes = parseInt(document.getElementById("mat-duration").value);

            try {
                if (editingMaterialId) {
                    const res = await fetchApi(`/api/materials/${encodeURIComponent(editingMaterialId)}`, {
                        method: "PUT",
                        body: JSON.stringify({ title, type, content_url, duration_minutes })
                    });
                    showToast(res.message, "success");
                } else {
                    const res = await fetchApi("/api/materials", {
                        method: "POST",
                        body: JSON.stringify({ material_id, course_id, title, type, content_url, duration_minutes })
                    });
                    showToast(res.message, "success");
                }
                closeModal("modal-material");
                loadMaterials();
            } catch (err) {
                showToast(err.message, "error");
            }
        });
    }
});
