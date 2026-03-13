/**
 * Multi-Tenant HR SaaS Dashboard — Frontend Client
 * Sets X-Org-Id header on every API call to demonstrate tenant isolation.
 */

// ── State ─────────────────────────────────────────────
let currentOrgId = null;
let organizations = [];

// ── API Client ────────────────────────────────────────
async function api(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (currentOrgId) {
        headers['X-Org-Id'] = String(currentOrgId);
    }
    const res = await fetch(path, { ...options, headers });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(err.detail || 'Request failed');
    }
    return res.json();
}

// ── Init ──────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    await loadOrganizations();
});

// ── Organizations ─────────────────────────────────────
async function loadOrganizations() {
    try {
        organizations = await api('/api/organizations');
        const select = document.getElementById('orgSelect');
        select.innerHTML = organizations.map(org =>
            `<option value="${org.id}">${org.name}</option>`
        ).join('');

        if (organizations.length > 0) {
            currentOrgId = organizations[0].id;
            select.value = currentOrgId;
            updateOrgBadge(organizations[0]);
            await loadAllData();
        }

        select.addEventListener('change', async (e) => {
            currentOrgId = parseInt(e.target.value);
            const org = organizations.find(o => o.id === currentOrgId);
            updateOrgBadge(org);
            await loadAllData();
        });
    } catch (err) {
        console.error('Failed to load organizations:', err);
    }
}

function updateOrgBadge(org) {
    const badge = document.getElementById('orgPlanBadge');
    badge.textContent = org.plan;
    badge.className = `org-plan-badge ${org.plan}`;
    document.getElementById('bannerOrgName').textContent = org.name;
    document.getElementById('dashOrgName').textContent = org.name;
}

// ── Load All Data ─────────────────────────────────────
async function loadAllData() {
    const main = document.querySelector('.main-content');
    main.style.opacity = '0.5';
    main.style.transition = 'opacity 0.15s ease';

    try {
        await Promise.all([
            loadStats(),
            loadEmployees(),
            loadAttendance(),
            loadLeaves(),
        ]);
    } catch (err) {
        console.error('Failed to load data:', err);
    }

    main.style.opacity = '1';
}

// ── Dashboard Stats ───────────────────────────────────
async function loadStats() {
    const stats = await api('/api/stats');

    animateNumber('statEmployees', stats.total_employees);
    animateNumber('statActive', stats.active_employees);
    animateNumber('statOnLeave', stats.on_leave);

    const avgSalary = stats.avg_salary;
    const el = document.getElementById('statAvgSalary');
    el.textContent = '$' + Math.round(avgSalary / 1000) + 'k';

    document.getElementById('empCount').textContent = stats.total_employees;
    document.getElementById('leaveCount').textContent = stats.pending_leaves;

    renderDeptChart(stats.departments, stats.total_employees);
    renderAttendanceChart(stats.today_attendance);
}

function animateNumber(elementId, target) {
    const el = document.getElementById(elementId);
    const current = parseInt(el.textContent) || 0;
    const diff = target - current;
    const steps = 20;
    const stepValue = diff / steps;
    let step = 0;

    const interval = setInterval(() => {
        step++;
        el.textContent = Math.round(current + stepValue * step);
        if (step >= steps) {
            el.textContent = target;
            clearInterval(interval);
        }
    }, 20);
}

function renderDeptChart(deptData, total) {
    const container = document.getElementById('deptChart');
    const deptColors = {
        engineering: 'in_progress',
        design: 'in_review',
        marketing: 'done',
        sales: 'todo',
        hr: 'in_progress',
        finance: 'in_review',
        operations: 'done',
        support: 'todo',
    };

    const entries = Object.entries(deptData).sort((a, b) => b[1] - a[1]);

    container.innerHTML = entries.map(([dept, count]) => {
        const pct = total > 0 ? (count / total * 100) : 0;
        const colorClass = deptColors[dept] || 'todo';
        return `
            <div class="bar-row">
                <span class="bar-label">${dept}</span>
                <div class="bar-track">
                    <div class="bar-fill ${colorClass}" style="width: 0%"></div>
                </div>
                <span class="bar-value">${count}</span>
            </div>
        `;
    }).join('');

    requestAnimationFrame(() => {
        setTimeout(() => {
            container.querySelectorAll('.bar-fill').forEach((bar, i) => {
                const count = entries[i][1];
                const pct = total > 0 ? (count / total * 100) : 0;
                bar.style.width = `${Math.max(pct, 5)}%`;
            });
        }, 50);
    });
}

function renderAttendanceChart(attData) {
    const container = document.getElementById('attendanceChart');
    const attConfig = [
        { key: 'present', label: 'Present', dotClass: 'medium' },
        { key: 'work_from_home', label: 'WFH', dotClass: 'low' },
        { key: 'late', label: 'Late', dotClass: 'high' },
        { key: 'absent', label: 'Absent', dotClass: 'urgent' },
        { key: 'half_day', label: 'Half Day', dotClass: 'high' },
    ];

    container.innerHTML = attConfig.map(a => {
        const count = attData[a.key] || 0;
        return `
            <div class="priority-item">
                <div class="priority-dot ${a.dotClass}"></div>
                <div class="priority-info">
                    <div class="priority-label">${a.label}</div>
                    <div class="priority-count">${count}</div>
                </div>
            </div>
        `;
    }).join('');
}

// ── Employees Table ───────────────────────────────────
async function loadEmployees() {
    const employees = await api('/api/employees');
    const tbody = document.getElementById('empTableBody');
    document.getElementById('empRecordCount').textContent = `${employees.length} records`;

    if (employees.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><div class="empty-icon">👥</div><p>No employees in this company</p></div></td></tr>`;
        return;
    }

    tbody.innerHTML = employees.map(e => `
        <tr>
            <td style="color: var(--text-muted); font-weight: 600;">#${e.id}</td>
            <td style="font-weight: 600;">${e.name}</td>
            <td style="color: var(--text-secondary);">${e.email}</td>
            <td><span class="status-badge active">${e.department}</span></td>
            <td style="color: var(--text-secondary);">${e.position}</td>
            <td><span class="status-badge ${e.status}">${formatStatus(e.status)}</span></td>
            <td><span style="color: var(--accent-blue); font-weight: 700;">${e.org_id}</span></td>
        </tr>
    `).join('');
}

// ── Attendance Table ──────────────────────────────────
async function loadAttendance() {
    const records = await api('/api/attendance');
    const tbody = document.getElementById('attTableBody');
    document.getElementById('attRecordCount').textContent = `${records.length} records`;

    if (records.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><div class="empty-icon">📋</div><p>No attendance records</p></div></td></tr>`;
        return;
    }

    tbody.innerHTML = records.map(a => `
        <tr>
            <td style="color: var(--text-muted); font-weight: 600;">#${a.id}</td>
            <td style="font-weight: 600;">${a.employee_name}</td>
            <td style="color: var(--text-secondary);">${formatDate(a.date)}</td>
            <td><span class="status-badge ${a.status}">${formatStatus(a.status)}</span></td>
            <td style="color: var(--text-secondary);">${a.check_in || '—'}</td>
            <td style="color: var(--text-secondary);">${a.check_out || '—'}</td>
            <td><span style="color: var(--accent-blue); font-weight: 700;">${a.org_id}</span></td>
        </tr>
    `).join('');
}

// ── Leave Requests Table ──────────────────────────────
async function loadLeaves() {
    const leaves = await api('/api/leaves');
    const tbody = document.getElementById('leaveTableBody');
    document.getElementById('leaveRecordCount').textContent = `${leaves.length} records`;

    if (leaves.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><div class="empty-icon">🏖️</div><p>No leave requests</p></div></td></tr>`;
        return;
    }

    const leaveStatusMap = {
        pending: 'in_review',
        approved: 'done',
        rejected: 'todo',
        cancelled: 'paused',
    };

    tbody.innerHTML = leaves.map(l => `
        <tr>
            <td style="color: var(--text-muted); font-weight: 600;">#${l.id}</td>
            <td style="font-weight: 600;">${l.employee_name}</td>
            <td><span class="priority-badge medium">${l.leave_type}</span></td>
            <td style="color: var(--text-secondary);">${formatDate(l.start_date)}</td>
            <td style="color: var(--text-secondary);">${formatDate(l.end_date)}</td>
            <td style="color: var(--text-secondary); max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${l.reason}</td>
            <td><span class="status-badge ${leaveStatusMap[l.status] || l.status}">${l.status}</span></td>
            <td><span style="color: var(--accent-blue); font-weight: 700;">${l.org_id}</span></td>
        </tr>
    `).join('');
}

// ── Tab Navigation ────────────────────────────────────
function switchTab(tabName) {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.tab === tabName);
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `tab-${tabName}`);
    });
}

// ── Utilities ─────────────────────────────────────────
function formatDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatStatus(status) {
    return status.replace(/_/g, ' ');
}
