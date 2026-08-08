/**
 * IaC Security Framework Dashboard — Chart.js Visualizations
 * Handles chart initialization for the Scan Details page.
 */

const SEVERITY_COLORS = {
    CRITICAL: '#dc2626',
    HIGH: '#ea580c',
    MEDIUM: '#ca8a04',
    LOW: '#2563eb',
    UNKNOWN: '#6b7280',
};

const CHART_OPTIONS = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: false // We use custom HTML legends if needed, or rely on the numbers in the UI
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
    cutout: '70%',
};

/**
 * Initialize the side-by-side pre/post deployment charts.
 * @param {Object} data - Chart data from Flask template containing pre/post counts.
 */
function initPrePostCharts(data) {
    if (!data) return;

    if (data.has_pre) {
        createDoughnutChart('preSeverityChart', data.pre_severity_counts);
        
        // Add sources ring chart for pre-deployment
        if (data.pre_source_counts) {
            createDoughnutChart('preSourceChart', data.pre_source_counts, {
                'CHECKOV': '#3b82f6',         // blue
                'REGO/CONFTEST': '#06b6d4',   // cyan
                'OTHER': '#9ca3af'            // gray
            });
        }
    }
    
    if (data.has_post) {
        createDoughnutChart('postSeverityChart', data.post_severity_counts);
    }
}

/**
 * Helper to create a standard severity or source doughnut chart
 */
function createDoughnutChart(canvasId, counts, customColors = null) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    // Filter out items with 0 count
    const labels = Object.keys(counts).filter(k => counts[k] > 0);
    const values = labels.map(k => counts[k]);
    
    let colors;
    if (customColors) {
        colors = labels.map(k => customColors[k] || '#9ca3af');
    } else {
        colors = labels.map(k => SEVERITY_COLORS[k] || SEVERITY_COLORS.UNKNOWN);
    }

    // Don't render empty charts
    if (labels.length === 0) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 4,
            }],
        },
        options: CHART_OPTIONS,
    });
}

