/**
 * Dashboard View Logic
 */

async function loadDashboard() {
    try {
        const stats = await fetchApi("/api/dashboard/stats");

        // KPI Counts
        const mongo = stats.mongodb?.counts || {};
        document.getElementById("kpi-students").textContent = mongo.students ?? 0;
        document.getElementById("kpi-courses").textContent = mongo.courses ?? 0;
        document.getElementById("kpi-instructors").textContent = mongo.instructors ?? 0;
        document.getElementById("kpi-materials").textContent = mongo.learning_materials ?? 0;

        const neo = stats.neo4j || {};
        document.getElementById("kpi-nodes").textContent = neo.total_nodes ?? 0;
        document.getElementById("kpi-rels").textContent = neo.total_relationships ?? 0;

        // Progress Summary
        const prog = stats.mongodb?.progress_summary || {};
        document.getElementById("stat-completed").textContent = prog.completed ?? 0;
        document.getElementById("stat-in-progress").textContent = prog.in_progress ?? 0;
        document.getElementById("stat-avg-completion").textContent = `${prog.overall_average_completion ?? 0}%`;

        // Recent Activity Table
        const recentTable = document.getElementById("dashboard-recent-table");
        if (stats.recent_activity && stats.recent_activity.length > 0) {
            recentTable.innerHTML = stats.recent_activity.map(item => {
                const badgeClass = item.status === "completed" ? "badge-success" : "badge-info";
                const lastAccessed = item.last_accessed ? new Date(item.last_accessed).toLocaleDateString() : "N/A";
                return `
                    <tr>
                        <td><strong>${escapeHtml(item.student_name || item.student_id)}</strong></td>
                        <td>${escapeHtml(item.course_title || item.course_id)}</td>
                        <td style="min-width: 140px;">
                            <div class="d-flex align-items-center gap-2">
                                <div class="progress-bar-container">
                                    <div class="progress-bar-fill ${item.status === 'completed' ? 'completed' : ''}" style="width: ${item.completion_percentage}%;"></div>
                                </div>
                                <span style="font-size: 11px; font-weight: 600;">${item.completion_percentage}%</span>
                            </div>
                        </td>
                        <td><span class="badge ${badgeClass}">${escapeHtml(item.status)}</span></td>
                        <td><span class="text-muted" style="font-size: 12px;">${lastAccessed}</span></td>
                    </tr>
                `;
            }).join("");
        } else {
            recentTable.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No progress records available.</td></tr>`;
        }
    } catch (err) {
        showToast(`Failed to load dashboard: ${err.message}`, "error");
    }
}
