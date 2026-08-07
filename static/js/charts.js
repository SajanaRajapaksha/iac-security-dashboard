/**
 * IaC Security Framework Dashboard — Chart.js Visualizations
 * All chart initialization functions for the main dashboard page.
 */

/* Color palette */
const COLORS = {
    primary: '#6366f1',
    primaryLight: '#818cf8',
    success: '#10b981',
    successLight: '#34d399',
    danger: '#dc2626',
    dangerLight: '#f87171',
    warning: '#f59e0b',
    warningLight: '#fbbf24',
    info: '#0ea5e9',
    infoLight: '#38bdf8',
    purple: '#8b5cf6',
    purpleLight: '#a78bfa',
    gray: '#6b7280',
    grayLight: '#9ca3af',
};

const SEVERITY_COLORS = {
    CRITICAL: '#dc2626',
    HIGH: '#ea580c',
    MEDIUM: '#ca8a04',
    LOW: '#2563eb',
    UNKNOWN: '#6b7280',
};

const SCANNER_COLORS = {
    Checkov: '#3b82f6',
    'Conftest/Rego': '#06b6d4',
    Prowler: '#8b5cf6',
};

/* Default Chart.js configuration */
const defaultOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'bottom',
            labels: {
                padding: 16,
                usePointStyle: true,
                pointStyleWidth: 10,
                font: {
                    family: "'Inter', sans-serif",
                    size: 11,
                },
            },
        },
        tooltip: {
            backgroundColor: '#1f2937',
            titleFont: { family: "'Inter', sans-serif", size: 12, weight: '600' },
            bodyFont: { family: "'Inter', sans-serif", size: 11 },
            padding: 12,
            cornerRadius: 8,
            displayColors: true,
        },
    },
};

/**
 * Initialize all dashboard charts.
 * @param {Object} data - Chart data from Flask template.
 */
function initDashboardCharts(data) {
    createRiskScoreChart(data);
    createSeverityChart(data);
    createScannerChart(data);
    createDecisionChart(data);
    createCategoryChart(data);
}

/**
 * Pre vs Post Risk Score — Bar Chart
 */
function createRiskScoreChart(data) {
    const ctx = document.getElementById('riskScoreChart');
    if (!ctx || !data.scan_labels || data.scan_labels.length === 0) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.scan_labels,
            datasets: [
                {
                    label: 'Pre-Deployment Score',
                    data: data.pre_scores,
                    backgroundColor: COLORS.primary,
                    borderColor: COLORS.primary,
                    borderWidth: 0,
                    borderRadius: 6,
                    barPercentage: 0.6,
                },
                {
                    label: 'Post-Deployment Score',
                    data: data.post_scores,
                    backgroundColor: COLORS.success,
                    borderColor: COLORS.success,
                    borderWidth: 0,
                    borderRadius: 6,
                    barPercentage: 0.6,
                },
            ],
        },
        options: {
            ...defaultOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1000,
                    grid: { color: 'rgba(0,0,0,0.04)' },
                    ticks: {
                        font: { family: "'Inter', sans-serif", size: 11 },
                        color: '#6b7280',
                    },
                    title: {
                        display: true,
                        text: 'Risk Score (0-1000)',
                        font: { family: "'Inter', sans-serif", size: 11, weight: '600' },
                        color: '#6b7280',
                    },
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        font: { family: "'JetBrains Mono', monospace", size: 10 },
                        color: '#6b7280',
                    },
                },
            },
        },
    });
}

/**
 * Severity Distribution — Doughnut Chart
 */
function createSeverityChart(data) {
    const ctx = document.getElementById('severityChart');
    if (!ctx || !data.severity_counts) return;

    const counts = data.severity_counts;
    const labels = Object.keys(counts).filter(k => counts[k] > 0);
    const values = labels.map(k => counts[k]);
    const colors = labels.map(k => SEVERITY_COLORS[k] || COLORS.gray);

    if (labels.length === 0) {
        ctx.parentElement.innerHTML = '<div class="empty-state py-4"><i class="bi bi-check-circle"></i><p>No findings</p></div>';
        return;
    }

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 6,
            }],
        },
        options: {
            ...defaultOptions,
            cutout: '65%',
            plugins: {
                ...defaultOptions.plugins,
                legend: {
                    ...defaultOptions.plugins.legend,
                    position: 'bottom',
                },
            },
        },
    });
}

/**
 * Scanner Distribution — Pie Chart
 */
function createScannerChart(data) {
    const ctx = document.getElementById('scannerChart');
    if (!ctx || !data.scanner_counts) return;

    const counts = data.scanner_counts;
    const labels = Object.keys(counts);
    const values = labels.map(k => counts[k]);
    const colors = labels.map(k => SCANNER_COLORS[k] || COLORS.grayLight);

    if (labels.length === 0) {
        ctx.parentElement.innerHTML = '<div class="empty-state py-4"><i class="bi bi-diagram-3"></i><p>No scanner data</p></div>';
        return;
    }

    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 6,
            }],
        },
        options: {
            ...defaultOptions,
            plugins: {
                ...defaultOptions.plugins,
                legend: {
                    ...defaultOptions.plugins.legend,
                    position: 'bottom',
                },
            },
        },
    });
}

/**
 * Final Decision Distribution — Doughnut Chart
 */
function createDecisionChart(data) {
    const ctx = document.getElementById('decisionChart');
    if (!ctx || !data.decision_counts) return;

    const DECISION_COLORS = {
        APPROVED: '#10b981',
        REVIEW_REQUIRED: '#f59e0b',
        URGENT_REVIEW: '#dc2626',
        DENIED: '#ef4444',
        NOT_AVAILABLE: '#9ca3af',
    };

    const counts = data.decision_counts;
    const labels = Object.keys(counts);
    const values = labels.map(k => counts[k]);
    const colors = labels.map(k => DECISION_COLORS[k] || COLORS.grayLight);

    if (labels.length === 0) {
        ctx.parentElement.innerHTML = '<div class="empty-state py-4"><i class="bi bi-check2-square"></i><p>No decisions</p></div>';
        return;
    }

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.map(l => l.replace(/_/g, ' ')),
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 6,
            }],
        },
        options: {
            ...defaultOptions,
            cutout: '60%',
        },
    });
}

/**
 * Security Categories — Horizontal Bar Chart
 * This chart is populated from findings if category data is available.
 */
function createCategoryChart(data) {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;

    // Category data is not aggregated at dashboard level from scan-summary.json.
    // We show an informational placeholder. The per-scan category breakdown
    // is available on the Scan Details page.
    ctx.parentElement.innerHTML =
        '<div class="empty-state py-4">' +
        '<i class="bi bi-tags"></i>' +
        '<p class="small text-muted mt-2">Category breakdown is available per-scan on the Scan Details page.</p>' +
        '</div>';
}
