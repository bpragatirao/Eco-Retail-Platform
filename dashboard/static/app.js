/**
 * Eco-Retail Dashboard — Application Logic
 * Handles API communication, stat bar rendering, animations, and page navigation.
 */

// ── Configuration ──────────────────────────────────────────────────────────
const API_BASE = window.location.origin;
const BAR_COLORS = ['#10b981', '#06b6d4', '#f59e0b', '#6366f1', '#f97316', '#3b82f6', '#ec4899'];

// ── State ──────────────────────────────────────────────────────────────────
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

// ── Stat Bar Renderer (reusable) ───────────────────────────────────────────
function renderStatBars(containerId, dataObj, valueFormatter = (v) => v.toLocaleString('en-IN')) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const entries = Object.entries(dataObj);
    if (entries.length === 0) {
        container.innerHTML = `<div class="empty-state" style="padding:var(--space-md)"><p>No data available</p></div>`;
        return;
    }

    const maxVal = Math.max(...entries.map(([, v]) => v));
    const categoryEmojis = { dairy: '🥛', produce: '🥬', bakery: '🍞', meat: '🍗', beverages: '🧃' };

    container.innerHTML = entries.map(([key, val], i) => {
        const pct = maxVal > 0 ? (val / maxVal) * 100 : 0;
        const color = BAR_COLORS[i % BAR_COLORS.length];
        const label = key.charAt(0).toUpperCase() + key.slice(1);
        const emoji = categoryEmojis[key.toLowerCase()] || '📊';

        return `
            <div class="stat-bar-item">
                <div class="stat-bar-header">
                    <span class="stat-bar-label">
                        <span class="stat-bar-label-dot" style="background:${color}"></span>
                        ${emoji} ${label}
                    </span>
                    <span class="stat-bar-value">${valueFormatter(val)}</span>
                </div>
                <div class="stat-bar-track">
                    <div class="stat-bar-fill" style="width:${pct}%; background:${color}"></div>
                </div>
            </div>
        `;
    }).join('');
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

        // Populate compact stats
        const el = (id) => document.getElementById(id);
        if (el('stat-products')) el('stat-products').textContent = overview.total_products || '—';
        if (el('stat-batches')) el('stat-batches').textContent = overview.active_batches || '—';
        if (el('stat-avg-risk')) el('stat-avg-risk').textContent = overview.avg_risk_score
            ? overview.avg_risk_score.toFixed(0)
            : '—';
        if (el('stat-total-txns')) el('stat-total-txns').textContent = overview.total_transactions
            ? overview.total_transactions.toLocaleString('en-IN')
            : '—';

        // Add critical class
        if (overview.critical_alerts > 0) {
            document.getElementById('metric-critical')?.classList.add('critical');
        }
    }

    if (revenue && revenue.category_revenue) {
        renderStatBars('overview-category-bars', revenue.category_revenue, (v) => '₹' + formatLargeNumber(v));
    }

    if (alerts) {
        document.getElementById('alert-count-badge').textContent = alerts.length;
        renderOverviewAlerts(alerts.slice(0, 5));
    }
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
        renderStatBars('analytics-waste-bars', waste.waste_by_category, (v) => `${v} units`);
    }

    if (revenue) {
        animateCounter('counter-avg-discount', revenue.avg_discount);
        animateCounter('counter-disc-txns', revenue.transactions_with_discount);
        if (revenue.category_revenue) {
            renderStatBars('analytics-revenue-bars', revenue.category_revenue, (v) => '₹' + formatLargeNumber(v));
        }
    }
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
