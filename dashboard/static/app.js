/**
 * Eco-Retail Dashboard — Application Logic
 * Handles API communication, chart rendering, animations, and page navigation.
 */

// ── Configuration ──────────────────────────────────────────────────────────
const API_BASE = window.location.origin;
const CHART_COLORS = {
    green: '#10b981',
    greenLight: 'rgba(16, 185, 129, 0.15)',
    teal: '#06b6d4',
    tealLight: 'rgba(6, 182, 212, 0.15)',
    yellow: '#f59e0b',
    yellowLight: 'rgba(245, 158, 11, 0.15)',
    red: '#ef4444',
    redLight: 'rgba(239, 68, 68, 0.15)',
    purple: '#6366f1',
    purpleLight: 'rgba(99, 102, 241, 0.15)',
    orange: '#f97316',
    blue: '#3b82f6',
    pink: '#ec4899',
    slate: '#64748b',
};

// Chart.js global defaults for dark theme
Chart.defaults.color = '#9ca3af';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.06)';
Chart.defaults.font.family = "'Inter', sans-serif";

// ── State ──────────────────────────────────────────────────────────────────
let chartInstances = {};
let currentPage = 'overview';

// ── API Helper ─────────────────────────────────────────────────────────────
async function apiFetch(endpoint) {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (err) {
        console.error(`API Error [${endpoint}]:`, err);
        return null;
    }
}

async function apiPost(endpoint, body) {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (err) {
        console.error(`API Error [POST ${endpoint}]:`, err);
        return null;
    }
}

// ── Animated Counter ───────────────────────────────────────────────────────
function animateCounter(elementId, targetValue, prefix = '', suffix = '', duration = 1200) {
    const el = document.getElementById(elementId);
    if (!el) return;

    const isFloat = targetValue % 1 !== 0;
    const startValue = 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // Ease-out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = startValue + (targetValue - startValue) * eased;

        if (targetValue >= 100000) {
            el.textContent = formatLargeNumber(current);
        } else if (isFloat) {
            el.textContent = current.toFixed(1);
        } else {
            el.textContent = Math.round(current).toLocaleString('en-IN');
        }

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

function formatLargeNumber(num) {
    if (num >= 10000000) return (num / 10000000).toFixed(2) + ' Cr';
    if (num >= 100000) return (num / 100000).toFixed(2) + ' L';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return Math.round(num).toLocaleString('en-IN');
}

// ── Page Navigation ────────────────────────────────────────────────────────
function switchPage(pageName) {
    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.querySelector(`[data-page="${pageName}"]`);
    if (activeBtn) activeBtn.classList.add('active');

    // Update page sections
    document.querySelectorAll('.page-section').forEach(sec => sec.classList.remove('active'));
    const activePage = document.getElementById(`page-${pageName}`);
    if (activePage) activePage.classList.add('active');

    currentPage = pageName;

    // Load page-specific data
    if (pageName === 'inventory') loadInventory();
    if (pageName === 'analytics') loadAnalytics();
    if (pageName === 'alerts') loadAlerts();
}

// Navigation event listeners
document.querySelectorAll('.nav-btn[data-page]').forEach(btn => {
    btn.addEventListener('click', () => switchPage(btn.dataset.page));
});

// ── Overview Page ──────────────────────────────────────────────────────────
async function loadOverview() {
    const [overview, revenue, alerts] = await Promise.all([
        apiFetch('/api/dashboard/overview'),
        apiFetch('/api/analytics/revenue'),
        apiFetch('/api/alerts'),
    ]);

    if (overview) {
        animateCounter('counter-revenue', overview.total_revenue);
        animateCounter('counter-recovered', overview.revenue_recovered);
        animateCounter('counter-waste', overview.total_waste_value);
        animateCounter('counter-critical', overview.critical_alerts);

        // Add critical class
        if (overview.critical_alerts > 0) {
            document.getElementById('metric-critical')?.classList.add('critical');
        }
    }

    if (revenue) {
        renderRevenueChart(revenue.daily_revenue);
        renderCategoryChart(revenue.category_revenue);
    }

    if (alerts) {
        document.getElementById('alert-count-badge').textContent = alerts.length;
        renderOverviewAlerts(alerts.slice(0, 5));
    }
}

function renderRevenueChart(dailyRevenue) {
    const ctx = document.getElementById('chart-revenue');
    if (!ctx) return;
    if (chartInstances['revenue']) chartInstances['revenue'].destroy();

    const labels = dailyRevenue.map(d => {
        const date = new Date(d.date);
        return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
    });
    const data = dailyRevenue.map(d => d.revenue);

    chartInstances['revenue'] = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Daily Revenue (₹)',
                data,
                borderColor: CHART_COLORS.green,
                backgroundColor: CHART_COLORS.greenLight,
                fill: true,
                tension: 0.4,
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: CHART_COLORS.green,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 12,
                    titleFont: { family: "'Outfit', sans-serif", weight: '600' },
                    callbacks: {
                        label: (ctx) => `₹${ctx.parsed.y.toLocaleString('en-IN')}`,
                    }
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxTicksLimit: 8, font: { size: 11 } },
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    ticks: {
                        font: { size: 11 },
                        callback: (v) => '₹' + formatLargeNumber(v),
                    },
                },
            },
            interaction: { intersect: false, mode: 'index' },
        }
    });
}

function renderCategoryChart(categoryRevenue) {
    const ctx = document.getElementById('chart-category');
    if (!ctx) return;
    if (chartInstances['category']) chartInstances['category'].destroy();

    const labels = Object.keys(categoryRevenue).map(c => c.charAt(0).toUpperCase() + c.slice(1));
    const data = Object.values(categoryRevenue);
    const colors = [CHART_COLORS.green, CHART_COLORS.teal, CHART_COLORS.yellow, CHART_COLORS.purple, CHART_COLORS.orange];

    chartInstances['category'] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: colors.slice(0, labels.length),
                borderColor: 'rgba(10, 15, 26, 0.8)',
                borderWidth: 3,
                hoverOffset: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 16,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: { size: 12 },
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: (ctx) => `₹${ctx.parsed.toLocaleString('en-IN')}`,
                    }
                },
            }
        }
    });
}

function renderOverviewAlerts(alerts) {
    const container = document.getElementById('overview-alerts');
    if (!container) return;

    if (!alerts || alerts.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">✅</div>
                <p>No critical alerts — inventory is healthy!</p>
            </div>
        `;
        return;
    }

    container.innerHTML = alerts.map(alert => `
        <div class="alert-item ${alert.risk_level}">
            <div class="alert-icon ${alert.risk_level}">
                ${alert.risk_level === 'critical' ? '🔴' : '🟡'}
            </div>
            <div class="alert-content">
                <div class="alert-title">${alert.product_name}</div>
                <div class="alert-desc">
                    ${alert.remaining_quantity} units · ${alert.days_to_expiry} day${alert.days_to_expiry !== 1 ? 's' : ''} left · Risk: ${alert.risk_score.toFixed(0)}
                </div>
            </div>
            <div>
                <div style="font-size:0.75rem;color:var(--text-muted)">₹${alert.current_price} → ₹${alert.suggested_price}</div>
                <span class="discount-badge ${alert.risk_level}" style="margin-top:4px;display:inline-block">
                    ${((1 - alert.suggested_price / alert.current_price) * 100).toFixed(0)}% off
                </span>
            </div>
        </div>
    `).join('');
}

// ── Pricing Simulator ──────────────────────────────────────────────────────
document.getElementById('simulator-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const btn = document.getElementById('btn-calculate');
    btn.classList.add('loading');
    btn.textContent = '⏳ Calculating...';

    const body = {
        stock: parseInt(document.getElementById('sim-stock').value),
        days_to_expiry: parseInt(document.getElementById('sim-expiry').value),
        base_price: parseFloat(document.getElementById('sim-price').value),
        category: document.getElementById('sim-category').value,
    };

    const result = await apiPost('/api/price/calculate', body);

    btn.classList.remove('loading');
    btn.textContent = '⚡ Calculate Dynamic Price';

    if (result) {
        renderSimulatorResult(result, body.base_price);
    } else {
        document.getElementById('simulator-result').innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">❌</div>
                <p>Error calculating price. Check API connection.</p>
            </div>
        `;
    }
});

function renderSimulatorResult(result, basePrice) {
    const container = document.getElementById('simulator-result');
    const riskLevel = result.waste_risk.risk_level;
    const riskScore = result.waste_risk.overall_score;

    let riskBarClass = 'safe';
    if (riskLevel === 'critical') riskBarClass = 'critical';
    else if (riskLevel === 'warning') riskBarClass = 'warning';

    container.innerHTML = `
        <div class="price-display">
            ${result.discount_pct > 0 ? `<div class="price-original">₹${basePrice.toFixed(2)}</div>` : ''}
            <div class="price-dynamic animate">₹${result.final_price.toFixed(2)}</div>
        </div>

        ${result.discount_pct > 0 ? `
            <span class="discount-badge ${riskLevel}">
                🏷️ ${result.discount_pct.toFixed(1)}% discount applied
            </span>
        ` : `
            <span class="discount-badge safe">✅ No discount needed</span>
        `}

        <div class="risk-meter">
            <div class="risk-meter-label">
                <span>Waste Risk</span>
                <span>${riskScore.toFixed(0)}% — ${riskLevel.toUpperCase()}</span>
            </div>
            <div class="risk-meter-bar">
                <div class="risk-meter-fill ${riskBarClass}" style="width: ${riskScore}%"></div>
            </div>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; width:100%; max-width:320px; margin-top:12px">
            <div style="text-align:center; padding:10px; background:var(--bg-glass); border-radius:var(--radius-sm)">
                <div style="font-size:0.7rem; color:var(--text-muted); text-transform:uppercase">Predicted Demand</div>
                <div style="font-family:var(--font-heading); font-size:1.2rem; font-weight:700">${result.predicted_demand.toFixed(0)} units</div>
            </div>
            <div style="text-align:center; padding:10px; background:var(--bg-glass); border-radius:var(--radius-sm)">
                <div style="font-size:0.7rem; color:var(--text-muted); text-transform:uppercase">Revenue at Risk</div>
                <div style="font-family:var(--font-heading); font-size:1.2rem; font-weight:700">₹${result.potential_revenue_at_risk.toLocaleString('en-IN')}</div>
            </div>
        </div>

        <div class="reasoning-text">${result.reasoning}</div>
    `;
}

// ── Inventory Page ─────────────────────────────────────────────────────────
async function loadInventory() {
    const inventory = await apiFetch('/api/inventory');
    const tbody = document.getElementById('inventory-tbody');
    const countBadge = document.getElementById('inventory-count');

    if (!inventory || inventory.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="8">
                <div class="empty-state">
                    <div class="empty-state-icon">📦</div>
                    <p>No active inventory batches</p>
                </div>
            </td></tr>
        `;
        countBadge.textContent = '0 batches';
        return;
    }

    countBadge.textContent = `${inventory.length} active batches`;

    tbody.innerHTML = inventory.map(item => {
        const riskLevel = item.risk_level || 'safe';
        const categoryEmojis = { dairy: '🥛', produce: '🥬', bakery: '🍞', meat: '🍗', beverages: '🧃' };
        const emoji = categoryEmojis[item.category] || '📦';

        return `
            <tr>
                <td><strong>${item.product_name}</strong></td>
                <td>${emoji} ${item.category}</td>
                <td>${item.quantity}</td>
                <td>${item.remaining_quantity}</td>
                <td>${item.expiry_date}</td>
                <td>
                    <span class="status-badge ${riskLevel}">
                        <span class="status-dot ${riskLevel}"></span>
                        ${item.days_to_expiry} day${item.days_to_expiry !== 1 ? 's' : ''}
                    </span>
                </td>
                <td>
                    <span style="font-weight:600; color:${
                        riskLevel === 'critical' ? 'var(--status-critical)' :
                        riskLevel === 'warning' ? 'var(--status-warning)' :
                        'var(--status-safe)'
                    }">${item.waste_risk_score?.toFixed(0) ?? '—'}</span>
                </td>
                <td>
                    <span class="status-badge ${riskLevel}">
                        ${riskLevel === 'critical' ? '🔴 Critical' :
                          riskLevel === 'warning' ? '🟡 Warning' : '🟢 Safe'}
                    </span>
                </td>
            </tr>
        `;
    }).join('');
}

// ── Analytics Page ─────────────────────────────────────────────────────────
async function loadAnalytics() {
    const [waste, revenue] = await Promise.all([
        apiFetch('/api/analytics/waste'),
        apiFetch('/api/analytics/revenue'),
    ]);

    if (waste) {
        animateCounter('counter-waste-qty', waste.total_waste_quantity);
        animateCounter('counter-waste-value', waste.total_value_lost);
        renderWasteCategoryChart(waste.waste_by_category);
        renderWasteReasonChart(waste.waste_by_reason);
    }

    if (revenue) {
        animateCounter('counter-avg-discount', revenue.avg_discount);
        animateCounter('counter-disc-txns', revenue.transactions_with_discount);
    }
}

function renderWasteCategoryChart(wasteByCategory) {
    const ctx = document.getElementById('chart-waste-category');
    if (!ctx) return;
    if (chartInstances['wasteCategory']) chartInstances['wasteCategory'].destroy();

    const labels = Object.keys(wasteByCategory).map(c => c.charAt(0).toUpperCase() + c.slice(1));
    const data = Object.values(wasteByCategory);
    const colors = [CHART_COLORS.red, CHART_COLORS.orange, CHART_COLORS.yellow, CHART_COLORS.purple, CHART_COLORS.blue];

    chartInstances['wasteCategory'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Units Wasted',
                data,
                backgroundColor: colors.slice(0, labels.length).map(c => c + '33'),
                borderColor: colors.slice(0, labels.length),
                borderWidth: 1,
                borderRadius: 6,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 12,
                },
            },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { font: { size: 11 } } },
                y: { grid: { display: false }, ticks: { font: { size: 12 } } },
            }
        }
    });
}

function renderWasteReasonChart(wasteByReason) {
    const ctx = document.getElementById('chart-waste-reason');
    if (!ctx) return;
    if (chartInstances['wasteReason']) chartInstances['wasteReason'].destroy();

    const labels = Object.keys(wasteByReason).map(c => c.charAt(0).toUpperCase() + c.slice(1));
    const data = Object.values(wasteByReason);
    const colors = [CHART_COLORS.red, CHART_COLORS.yellow, CHART_COLORS.blue];

    chartInstances['wasteReason'] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: colors.slice(0, labels.length),
                borderColor: 'rgba(10, 15, 26, 0.8)',
                borderWidth: 3,
                hoverOffset: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 16, usePointStyle: true, pointStyle: 'circle', font: { size: 12 } }
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: (ctx) => `${ctx.parsed} units`,
                    }
                },
            }
        }
    });
}

// ── Alerts Page ────────────────────────────────────────────────────────────
async function loadAlerts() {
    const alerts = await apiFetch('/api/alerts');
    const container = document.getElementById('alerts-list');
    const badge = document.getElementById('alerts-total-badge');

    if (!alerts || alerts.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">✅</div>
                <p>No near-expiry alerts. All inventory is healthy!</p>
            </div>
        `;
        badge.textContent = '0 alerts';
        return;
    }

    badge.textContent = `${alerts.length} alert${alerts.length !== 1 ? 's' : ''}`;

    container.innerHTML = alerts.map(alert => `
        <div class="alert-item ${alert.risk_level}">
            <div class="alert-icon ${alert.risk_level}">
                ${alert.risk_level === 'critical' ? '🔴' : '🟡'}
            </div>
            <div class="alert-content">
                <div class="alert-title">${alert.product_name}</div>
                <div class="alert-desc">
                    ${alert.remaining_quantity} units remaining · Expires in ${alert.days_to_expiry} day${alert.days_to_expiry !== 1 ? 's' : ''}
                    <br>
                    <span style="color: var(--text-secondary)">Risk Score: <strong>${alert.risk_score.toFixed(0)}</strong> — ${alert.recommendation}</span>
                </div>
            </div>
            <div style="text-align:right; min-width:120px">
                <div style="font-size:0.8rem; color:var(--text-muted)">Price Suggestion</div>
                <div style="font-size:0.85rem">
                    <span style="text-decoration:line-through; color:var(--text-muted)">₹${alert.current_price}</span>
                    → <strong style="color:var(--text-accent)">₹${alert.suggested_price}</strong>
                </div>
                <span class="discount-badge ${alert.risk_level}" style="margin-top:6px; display:inline-block">
                    ${((1 - alert.suggested_price / alert.current_price) * 100).toFixed(0)}% off
                </span>
            </div>
        </div>
    `).join('');
}

// ── Initialize ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadOverview();
});
