// ClearLease MVP - Frontend JavaScript
// Handles API communication and UI updates

const API_ENDPOINT = 'https://api.clearlease.org/analyze';

// DOM Elements
const leaseTextarea = document.getElementById('leaseText');
const analyzeButton = document.getElementById('analyzeButton');
const resultsSection = document.getElementById('resultsSection');
const riskItemsContainer = document.getElementById('riskItems');
const overviewContainer = document.getElementById('overview');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const errorMessage = document.getElementById('errorMessage');

// Event Listeners
analyzeButton.addEventListener('click', handleAnalyze);

// Handle Enter key in textarea (Ctrl+Enter or Cmd+Enter)
leaseTextarea.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        handleAnalyze();
    }
});

/**
 * Main analysis handler
 */
async function handleAnalyze() {
    const leaseText = leaseTextarea.value.trim();

    // Validation
    if (!leaseText) {
        showError('Please paste your lease agreement text before analyzing.');
        return;
    }

    if (leaseText.length < 50) {
        showError('Please provide a longer lease agreement text (at least 50 characters).');
        return;
    }

    // Reset UI
    hideAllSections();
    showLoading();
    analyzeButton.disabled = true;

    try {
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: leaseText
            })
        });

        if (!response.ok) {
            throw new Error(`Analysis failed: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        displayResults(data);

    } catch (error) {
        console.error('Analysis error:', error);
        showError(`Unable to analyze your lease. Please try again later. ${error.message}`);
    } finally {
        hideLoading();
        analyzeButton.disabled = false;
    }
}

/**
 * Display analysis results
 */
function displayResults(data) {
    // Hide loading and error states
    hideAllSections();

    // Display overview if available
    if (data.overview) {
        displayOverview(data.overview);
    }

    // Display risk items
    const riskItems = extractRiskItems(data);
    if (riskItems.length > 0) {
        displayRiskItems(riskItems);
    } else {
        showNoRisksFound();
    }

    // Show results section
    resultsSection.style.display = 'block';

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Extract risk items from API response
 * Handles different response formats (key_findings, risk_items, etc.)
 */
function extractRiskItems(data) {
    const riskItems = [];

    // Try key_findings first (gateway format)
    if (data.key_findings && Array.isArray(data.key_findings)) {
        data.key_findings.forEach(item => {
            if (item.title && item.message) {
                riskItems.push({
                    title: item.title,
                    message: item.message,
                    severity: item.severity || item.intensity || 'medium',
                    action: item.user_action || null,
                    risk_code: item.risk_code || null
                });
            }
        });
    }

    // Try risk_items (analysis format)
    if (data.risk_items && Array.isArray(data.risk_items)) {
        data.risk_items.forEach(item => {
            riskItems.push({
                title: item.description || item.risk_code || 'Risk Item',
                message: item.description || 'A potential risk was identified.',
                severity: item.severity || 'medium',
                action: null,
                risk_code: item.risk_code || null
            });
        });
    }

    // Try details.v0.explanation_blocks
    if (data.details && data.details.v0 && data.details.v0.explanation_blocks) {
        data.details.v0.explanation_blocks.forEach(block => {
            riskItems.push({
                title: block.title,
                message: block.message,
                severity: block.severity || 'medium',
                action: block.user_action || null,
                risk_code: block.risk_code || null
            });
        });
    }

    // Deduplicate by title (simple deduplication)
    const seen = new Set();
    return riskItems.filter(item => {
        if (seen.has(item.title)) {
            return false;
        }
        seen.add(item.title);
        return true;
    }).slice(0, 5); // Limit to 5 items for MVP
}

/**
 * Display overview section
 */
function displayOverview(overview) {
    if (!overview) return;

    let html = '';
    
    if (overview.attention_level) {
        html += `<div class="overview-attention">Attention Level: ${overview.attention_level}</div>`;
    }
    
    if (overview.summary) {
        html += `<div class="overview-text">${escapeHtml(overview.summary)}</div>`;
    }

    overviewContainer.innerHTML = html;
    overviewContainer.style.display = 'block';
}

/**
 * Display risk items
 */
function displayRiskItems(riskItems) {
    if (riskItems.length === 0) {
        showNoRisksFound();
        return;
    }

    riskItemsContainer.innerHTML = riskItems.map(item => {
        const severityClass = normalizeSeverity(item.severity);
        const severityLabel = severityClass.charAt(0).toUpperCase() + severityClass.slice(1);

        return `
            <div class="risk-item severity-${severityClass}">
                <div class="risk-item-header">
                    <div class="risk-item-title">${escapeHtml(item.title)}</div>
                    <div class="risk-item-severity ${severityClass}">${severityLabel}</div>
                </div>
                <div class="risk-item-message">${escapeHtml(item.message)}</div>
                ${item.action ? `<div class="risk-item-action">Recommended: ${escapeHtml(item.action)}</div>` : ''}
            </div>
        `;
    }).join('');
}

/**
 * Show no risks found message
 */
function showNoRisksFound() {
    riskItemsContainer.innerHTML = `
        <div class="risk-item">
            <div class="risk-item-message" style="text-align: center; color: #666666; padding: 2rem;">
                No significant risk items were identified in your lease agreement.
            </div>
        </div>
    `;
}

/**
 * Normalize severity values
 */
function normalizeSeverity(severity) {
    if (!severity) return 'medium';
    const s = severity.toLowerCase();
    if (['high', 'critical'].includes(s)) return 'high';
    if (['low'].includes(s)) return 'low';
    return 'medium';
}

/**
 * Show loading state
 */
function showLoading() {
    loadingState.style.display = 'block';
}

/**
 * Hide loading state
 */
function hideLoading() {
    loadingState.style.display = 'none';
}

/**
 * Show error state
 */
function showError(message) {
    hideAllSections();
    errorMessage.textContent = message;
    errorState.style.display = 'block';
}

/**
 * Hide all sections
 */
function hideAllSections() {
    resultsSection.style.display = 'none';
    loadingState.style.display = 'none';
    errorState.style.display = 'none';
    overviewContainer.style.display = 'none';
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

