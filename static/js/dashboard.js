/**
 * IaC Security Framework Dashboard — Main JavaScript
 * Handles sidebar navigation, filtering, and general UI interactions.
 */

document.addEventListener('DOMContentLoaded', function () {
    initSidebarNavigation();
});

/**
 * Initialize sidebar navigation — dynamically update findings/evidence links
 * based on the most recent scan ID if available.
 */
function initSidebarNavigation() {
    // Try to extract scan_id from the current URL
    const pathMatch = window.location.pathname.match(/\/scans\/([A-Za-z0-9\-]+)/);
    const scanId = pathMatch ? pathMatch[1] : null;

    const findingsLink = document.getElementById('nav-findings');
    const evidenceLink = document.getElementById('nav-evidence');
    const riskLink = document.getElementById('nav-risk');

    if (scanId) {
        if (findingsLink) findingsLink.href = '/scans/' + scanId + '/findings';
        if (evidenceLink) evidenceLink.href = '/scans/' + scanId + '/evidence';
        if (riskLink) riskLink.href = '/scans/' + scanId;
    } else {
        // Link to scans page if no specific scan is selected
        if (findingsLink) findingsLink.href = '/scans';
        if (evidenceLink) evidenceLink.href = '/scans';
        if (riskLink) riskLink.href = '/scans';
    }
}
