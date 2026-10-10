/**
 * API Client & Toast Notification System
 */

async function fetchApi(endpoint, options = {}) {
    const config = {
        headers: {
            "Content-Type": "application/json",
            ...options.headers
        },
        ...options
    };

    try {
        const response = await fetch(endpoint, config);
        const data = await response.json().catch(() => null);

        if (!response.ok) {
            const errorMsg = data && data.detail ? data.detail : `HTTP ${response.status}: ${response.statusText}`;
            throw new Error(errorMsg);
        }

        return data;
    } catch (err) {
        console.error(`API Error on [${endpoint}]:`, err);
        throw err;
    }
}

function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    let icon = "fa-info-circle";
    if (type === "success") icon = "fa-circle-check";
    if (type === "error") icon = "fa-circle-exclamation";

    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function escapeHtml(str) {
    if (typeof str !== "string") return str;
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add("active");
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("active");
}

// Global modal close handlers
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".modal-close, .modal-close-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const modal = btn.closest(".modal");
            if (modal) modal.classList.remove("active");
        });
    });

    // Close modal on backdrop click
    document.querySelectorAll(".modal").forEach(modal => {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) modal.classList.remove("active");
        });
    });
});
