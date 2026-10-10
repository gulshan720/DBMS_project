/**
 * Application Core Router & Event Coordinator
 */

const VIEWS = {
    dashboard: {
        title: "Dashboard Overview",
        subtitle: "Live system telemetry from MongoDB Document Store & Neo4j Graph Database",
        load: loadDashboard
    },
    students: {
        title: "Student Management",
        subtitle: "Registered learners, enrollments, and academic profiles",
        load: loadStudents
    },
    courses: {
        title: "Course Catalog",
        subtitle: "Technical curriculum categorized across domains with difficulty ratings",
        load: loadCourses
    },
    materials: {
        title: "Learning Materials",
        subtitle: "Multi-format educational content (Videos, PDF guides, Articles)",
        load: loadMaterials
    },
    quizzes: {
        title: "Assessments & Progress",
        subtitle: "Course quizzes, question sets, completion percentages, and attempt logs",
        load: () => {
            loadQuizzes();
            loadProgressRecords();
        }
    },
    analytics: {
        title: "Analytics & Aggregation",
        subtitle: "MongoDB 5-stage aggregation pipelines and live query explain plans",
        load: loadAnalytics
    },
    graph: {
        title: "Graph Knowledge Insights",
        subtitle: "Neo4j property graph traversals, prerequisite paths, and collaborative recommendations",
        load: loadGraphInsights
    }
};

function navigateTo(viewName) {
    if (!VIEWS[viewName]) viewName = "dashboard";

    // Update URL hash
    window.location.hash = viewName;

    // Update Nav Links
    document.querySelectorAll(".nav-item").forEach(item => {
        item.classList.toggle("active", item.dataset.view === viewName);
    });

    // Update Views
    document.querySelectorAll(".view-panel").forEach(panel => {
        panel.classList.toggle("active", panel.id === `view-${viewName}`);
    });

    // Update Page Headings
    const viewConfig = VIEWS[viewName];
    document.getElementById("page-heading").textContent = viewConfig.title;
    document.getElementById("page-subheading").textContent = viewConfig.subtitle;

    // Load View Data
    if (typeof viewConfig.load === "function") {
        viewConfig.load();
    }
}

async function checkDatabaseHealth() {
    const mongoDot = document.getElementById("mongo-dot");
    const neoDot = document.getElementById("neo-dot");

    try {
        const health = await fetchApi("/api/health");
        const mongo = health.databases?.mongodb?.status === "connected";
        const neo = health.databases?.neo4j?.status === "connected";

        if (mongoDot) {
            mongoDot.className = `dot ${mongo ? 'connected' : 'error'}`;
            mongoDot.title = `MongoDB: ${health.databases?.mongodb?.latency_ms || 0}ms (${health.databases?.mongodb?.mode || 'OK'})`;
        }
        if (neoDot) {
            neoDot.className = `dot ${neo ? 'connected' : 'error'}`;
            neoDot.title = `Neo4j: ${health.databases?.neo4j?.latency_ms || 0}ms`;
        }
    } catch (err) {
        if (mongoDot) mongoDot.className = "dot error";
        if (neoDot) neoDot.className = "dot error";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // Hash routing
    const initialView = window.location.hash.replace("#", "") || "dashboard";
    navigateTo(initialView);

    window.addEventListener("hashchange", () => {
        const hashView = window.location.hash.replace("#", "") || "dashboard";
        navigateTo(hashView);
    });

    // Nav click handlers
    document.querySelectorAll(".nav-item").forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            const view = link.dataset.view;
            navigateTo(view);
        });
    });

    // Global Refresh Button
    const refreshBtn = document.getElementById("btn-refresh");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
            const currentView = window.location.hash.replace("#", "") || "dashboard";
            showToast("Refreshing live database telemetry...", "info");
            checkDatabaseHealth();
            if (VIEWS[currentView]?.load) VIEWS[currentView].load();
        });
    }

    // Generic tab headers handler
    document.querySelectorAll(".tabs-header").forEach(header => {
        header.querySelectorAll(".tab-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const targetTabId = btn.dataset.tab;
                const container = header.parentElement;

                header.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");

                container.querySelectorAll(".tab-content").forEach(tc => {
                    tc.classList.toggle("active", tc.id === targetTabId);
                });
            });
        });
    });

    // Initial DB Health check and periodic polling every 30s
    checkDatabaseHealth();
    setInterval(checkDatabaseHealth, 30000);
});
