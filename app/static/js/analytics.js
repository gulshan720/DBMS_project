/**
 * Analytics View Logic (MongoDB Aggregations & Index Explain Plans)
 */

async function loadAnalytics() {
    loadAgg1();
    loadAgg2();
    loadAgg3();
    loadAgg4();
    loadAgg5();
    loadIndexingExplain();
}

async function loadAgg1() {
    const tbody = document.getElementById("agg1-table-body");
    if (!tbody) return;
    try {
        const data = await fetchApi("/api/analytics/course-completion");
        tbody.innerHTML = data.map(item => `
            <tr>
                <td><strong>${escapeHtml(item.course_id)}</strong></td>
                <td>${escapeHtml(item.title)}</td>
                <td><span class="badge badge-primary">${escapeHtml(item.category)}</span></td>
                <td>
                    <div class="d-flex align-items-center gap-2">
                        <div class="progress-bar-container" style="width: 120px;">
                            <div class="progress-bar-fill ${item.average_completion >= 80 ? 'completed' : ''}" style="width: ${item.average_completion}%;"></div>
                        </div>
                        <strong>${item.average_completion}%</strong>
                    </div>
                </td>
                <td>${item.enrolled_count} students</td>
            </tr>
        `).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-danger">Failed to load: ${escapeHtml(err.message)}</td></tr>`;
    }
}

async function loadAgg2() {
    const tbody = document.getElementById("agg2-table-body");
    if (!tbody) return;
    try {
        const data = await fetchApi("/api/analytics/top-students");
        tbody.innerHTML = data.map((item, idx) => `
            <tr>
                <td><span class="badge ${idx === 0 ? 'badge-warning' : 'badge-primary'}">#${idx + 1} ${escapeHtml(item.student_id)}</span></td>
                <td><strong>${escapeHtml(item.name)}</strong></td>
                <td>${escapeHtml(item.email)}</td>
                <td><span class="badge badge-success" style="font-size: 13px;">${item.completed_courses_count} course(s) completed</span></td>
            </tr>
        `).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-danger">Failed to load: ${escapeHtml(err.message)}</td></tr>`;
    }
}

async function loadAgg3() {
    const tbody = document.getElementById("agg3-table-body");
    if (!tbody) return;
    try {
        const data = await fetchApi("/api/analytics/revenue");
        tbody.innerHTML = data.map(item => `
            <tr>
                <td><strong>${escapeHtml(item.course_id)}</strong></td>
                <td>${escapeHtml(item.title)}</td>
                <td><span class="badge badge-primary">${escapeHtml(item.category)}</span></td>
                <td>₹${(item.price || 0).toLocaleString()}</td>
                <td>${item.enrolled_students} enrolled</td>
                <td><strong class="text-success" style="color: #059669;">₹${(item.estimated_revenue || 0).toLocaleString()}</strong></td>
            </tr>
        `).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-danger">Failed to load: ${escapeHtml(err.message)}</td></tr>`;
    }
}

async function loadAgg4() {
    const tbody = document.getElementById("agg4-table-body");
    if (!tbody) return;
    try {
        const data = await fetchApi("/api/analytics/quiz-performance");
        tbody.innerHTML = data.map(item => `
            <tr>
                <td><strong>${escapeHtml(item.quiz_id)}</strong></td>
                <td>${escapeHtml(item.title)}</td>
                <td><span class="badge badge-primary">${escapeHtml(item.course_id)}</span></td>
                <td>${item.total_points} pts</td>
                <td><span class="badge badge-info" style="font-size: 12px;">Avg: ${item.average_score}</span></td>
                <td>${item.attempts} attempts</td>
            </tr>
        `).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-danger">Failed to load: ${escapeHtml(err.message)}</td></tr>`;
    }
}

async function loadAgg5() {
    const tbody = document.getElementById("agg5-table-body");
    if (!tbody) return;
    try {
        const data = await fetchApi("/api/analytics/materials-distribution");
        tbody.innerHTML = data.map(item => {
            let icon = "fa-file";
            if (item.material_type === "video") icon = "fa-video";
            else if (item.material_type === "pdf") icon = "fa-file-pdf";
            else if (item.material_type === "article") icon = "fa-newspaper";

            return `
                <tr>
                    <td><strong><i class="fa-solid ${icon}"></i> ${escapeHtml(item.material_type.toUpperCase())}</strong></td>
                    <td><span class="badge badge-primary" style="font-size: 13px;">${item.count} items</span></td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="2" class="text-danger">Failed to load: ${escapeHtml(err.message)}</td></tr>`;
    }
}

async function loadIndexingExplain() {
    const box = document.getElementById("explain-box");
    const list = document.getElementById("active-indexes-list");
    if (!box || !list) return;

    try {
        const data = await fetchApi("/api/analytics/indexing-explain");
        const comp = data.execution_comparison;

        box.innerHTML = `
            <div style="display: flex; gap: 20px; align-items: stretch; margin-bottom: 16px;">
                <div style="flex: 1; background: #fee2e2; border: 1px solid #f87171; border-radius: 8px; padding: 14px;">
                    <h5 style="color: #991b1b; margin-bottom: 6px;"><i class="fa-solid fa-triangle-exclamation"></i> Without Index (Stage: COLLSCAN)</h5>
                    <p style="font-size: 12px; color: #7f1d1d; margin: 0;"><strong>${escapeHtml(comp.without_index_stage)}</strong></p>
                </div>
                <div style="display: flex; align-items: center; font-size: 20px; color: var(--text-muted);"><i class="fa-solid fa-arrow-right"></i></div>
                <div style="flex: 1; background: #d1fae5; border: 1px solid #34d399; border-radius: 8px; padding: 14px;">
                    <h5 style="color: #065f46; margin-bottom: 6px;"><i class="fa-solid fa-circle-check"></i> With Index on 'category' (Stage: IXSCAN)</h5>
                    <p style="font-size: 12px; color: #064e3b; margin: 0;"><strong>Stage: ${escapeHtml(comp.with_index_stage)}</strong><br>Index Utilized: <code>${escapeHtml(comp.index_utilized)}</code></p>
                </div>
            </div>
            <div style="background: #eef2ff; border-left: 4px solid #6366f1; padding: 10px 14px; font-size: 12px; color: #3730a3; border-radius: 4px;">
                <strong>Performance Impact:</strong> ${escapeHtml(comp.performance_gain)}
            </div>
        `;

        // Active indexes table
        const indexHtml = Object.entries(data.active_indexes).map(([col, idxList]) => `
            <div class="mb-3">
                <h5 class="mb-1"><code>${escapeHtml(col)}</code> Collection</h5>
                <ul style="padding-left: 20px; font-size: 12px; color: var(--text-secondary);">
                    ${idxList.map(idx => `<li><code>${escapeHtml(idx.name)}</code> (${idx.unique ? 'Unique' : 'Standard'}) - Keys: ${JSON.stringify(idx.keys)}</li>`).join("")}
                </ul>
            </div>
        `).join("");

        list.innerHTML = indexHtml;
    } catch (err) {
        box.innerHTML = `<p class="text-danger">Failed to load explain plan: ${escapeHtml(err.message)}</p>`;
    }
}
