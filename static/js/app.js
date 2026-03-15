/**
 * TenantHR — in-memory token only (no localStorage — XSS safe)
 */

let authToken = null;
let currentOrgId = null;
let currentUser = null;
let employeeCache = [];

// ── API ───────────────────────────────────────────────
async function api(path, options = {}) {
    if (!authToken) { handleLogout(); throw new Error('Not authenticated'); }
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    headers['Authorization'] = `Bearer ${authToken}`;
    const res = await fetch(path, { ...options, headers });
    if (res.status === 401) { handleLogout(); throw new Error('Session expired'); }
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(err.detail || 'Request failed');
    }
    return res.json();
}

// ── Init ──────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const today = new Date();
    const weekAgo = new Date(today); weekAgo.setDate(today.getDate() - 7);
    const fmt = d => d.toISOString().split('T')[0];
    const fromEl = document.getElementById('attDateFrom');
    const toEl   = document.getElementById('attDateTo');
    if (fromEl) fromEl.value = fmt(weekAgo);
    if (toEl)   toEl.value   = fmt(today);
    // today date in topbar
    const todayEl = document.getElementById('todayDate');
    if (todayEl) todayEl.textContent = today.toLocaleDateString('en-US', { weekday:'short', month:'short', day:'numeric' });
});

// ── Login ─────────────────────────────────────────────
function fillLogin(email) {
    document.getElementById('loginEmail').value = email;
    document.getElementById('loginPassword').value = 'password123';
}

async function handleLogin(e) {
    e.preventDefault();
    const email    = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    const errorEl  = document.getElementById('loginError');
    const btn      = document.getElementById('loginBtn');

    if (!email || !password) {
        errorEl.textContent = 'Please enter both email and password.';
        errorEl.style.display = 'block'; return;
    }
    try {
        errorEl.style.display = 'none';
        btn.disabled = true; btn.textContent = 'Signing in…';

        const res = await fetch('/api/auth/login', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({ email, password }),
        });
        if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Login failed'); }

        const data = await res.json();
        authToken    = data.access_token;
        currentOrgId = data.org_id;
        currentUser  = { name: data.employee_name, org_id: data.org_id, org_name: data.org_name, role: data.employee_role };
        showDashboard();
    } catch (err) {
        errorEl.textContent = err.message; errorEl.style.display = 'block';
    } finally {
        btn.disabled = false; btn.textContent = 'Sign in →';
    }
}

function handleLogout() {
    authToken = null; currentOrgId = null; currentUser = null; employeeCache = [];
    document.getElementById('loginScreen').style.display  = 'flex';
    document.getElementById('sidebar').style.display      = 'none';
    document.getElementById('mainContent').style.display  = 'none';
    document.getElementById('mobileHeader').style.display = 'none';
}

async function showDashboard() {
    document.getElementById('loginScreen').style.display  = 'none';
    document.getElementById('sidebar').style.display      = 'flex';
    document.getElementById('mainContent').style.display  = 'flex';
    document.getElementById('mobileHeader').style.display = 'flex';

    // Populate static UI elements
    const initials = currentUser.name.split(' ').map(p => p[0]).join('').toUpperCase().slice(0,2);
    const adminRoles = ['manager','director','vp','cxo'];
    const isAdmin    = adminRoles.includes(currentUser.role);

    document.getElementById('currentOrgDisplay').textContent = currentUser.org_name;
    document.getElementById('loggedInUser').textContent      = currentUser.name;
    document.getElementById('userRoleBadge').textContent     = currentUser.role;
    document.getElementById('sfAvatar').textContent          = initials;
    document.getElementById('topbarOrg').textContent         = currentUser.org_name;
    document.getElementById('topbarUserName').textContent    = currentUser.name;
    document.getElementById('topbarAvatar').textContent      = initials;
    document.getElementById('dashGreetName').textContent     = currentUser.name.split(' ')[0];
    document.getElementById('dashOrgName').textContent       = currentUser.org_name;

    // Greeting time of day
    const hour = new Date().getHours();
    const greet = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
    const greetEl = document.getElementById('dashGreetTime');
    if (greetEl) greetEl.textContent = greet;

    // Date chip
    const chipEl = document.getElementById('dashDateChip');
    if (chipEl) chipEl.textContent = new Date().toLocaleDateString('en-US', { weekday:'short', month:'short', day:'numeric', year:'numeric' });

    // Today date in attendance header
    const todayEl = document.getElementById('todayDate');
    if (todayEl) todayEl.textContent = new Date().toLocaleDateString('en-US', { weekday:'short', month:'short', day:'numeric' });
    if (addBtn) addBtn.style.display = isAdmin ? '' : 'none';

    await loadAllData();
}

// ── Load all ──────────────────────────────────────────
async function loadAllData() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = 'flex';
    try {
        await Promise.all([loadStats(), loadEmployees(), loadAttendance(), loadLeaves()]);
    } catch(e) { console.error(e); }
    finally { overlay.style.display = 'none'; }
}

// ── Stats ─────────────────────────────────────────────
async function loadStats() {
    try {
        const s = await api('/api/stats');
        animateNumber('statEmployees', s.total_employees);
        animateNumber('statActive',    s.active_employees);
        animateNumber('statOnLeave',   s.on_leave);
        animateNumber('statPendingLeaves', s.pending_leaves);
        document.getElementById('statAvgSalary').textContent = '$' + Math.round(s.avg_salary / 1000) + 'k';
        document.getElementById('empCount').textContent   = s.total_employees;
        document.getElementById('leaveCount').textContent = s.pending_leaves;

        const metaEl = document.getElementById('totalEmpMeta');
        if (metaEl) metaEl.textContent = s.total_employees + ' people';

        // Progress bars
        if (s.total_employees > 0) {
            const activePct = Math.round(s.active_employees / s.total_employees * 100);
            const leavePct  = Math.round(s.on_leave / s.total_employees * 100);
            setTimeout(() => {
                const ap = document.getElementById('activeProgress');
                const lp = document.getElementById('leaveProgress');
                if (ap) ap.style.width = activePct + '%';
                if (lp) lp.style.width = leavePct + '%';
            }, 200);
        }

        // Mini spark bars (decorative, uses dept distribution as shape)
        const sparkEl = document.getElementById('sparkTotal');
        if (sparkEl && s.departments) {
            const vals = Object.values(s.departments);
            const max  = Math.max(...vals, 1);
            const heights = [60, 80, 50, 100]; // arbitrary visual rhythm
            sparkEl.innerHTML = heights.map((h, i) => {
                const pct = vals[i] ? Math.max(Math.round(vals[i] / max * h), 15) : h * 0.3;
                return `<div class="kpi-spark-bar" style="height:${pct}%;"></div>`;
            }).join('');
        }

        renderDeptChart(s.departments, s.total_employees);
        renderAttendanceChart(s.today_attendance);
    } catch(e) { console.error('Stats:', e); }
}

function animateNumber(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    const from = parseInt(el.textContent) || 0;
    const diff = target - from, steps = 20, step_v = diff / steps;
    let step = 0;
    const iv = setInterval(() => {
        step++;
        el.textContent = Math.round(from + step_v * step);
        if (step >= steps) { el.textContent = target; clearInterval(iv); }
    }, 20);
}

function renderDeptChart(deptData, total) {
    const container = document.getElementById('deptChart');
    if (!container) return;
    const colorClasses = ['in_progress','in_review','done','todo','in_progress','in_review','done','todo'];
    const entries = Object.entries(deptData).sort((a,b) => b[1] - a[1]);
    container.innerHTML = entries.map(([dept, count], i) => `
        <div class="bar-row">
            <span class="bar-label">${dept}</span>
            <div class="bar-track"><div class="bar-fill ${colorClasses[i%colorClasses.length]}" style="width:0%"></div></div>
            <span class="bar-value">${count}</span>
        </div>`).join('');
    requestAnimationFrame(() => setTimeout(() => {
        container.querySelectorAll('.bar-fill').forEach((bar, i) => {
            bar.style.width = `${Math.max(total > 0 ? entries[i][1]/total*100 : 0, 5)}%`;
        });
    }, 50));
}

function renderAttendanceChart(attData) {
    const container = document.getElementById('attendanceChart');
    if (!container) return;
    const items = [
        {key:'present',        label:'Present',   cls:'present'},
        {key:'work_from_home', label:'WFH',        cls:'wfh'},
        {key:'late',           label:'Late',       cls:'late'},
        {key:'absent',         label:'Absent',     cls:'absent'},
        {key:'half_day',       label:'Half day',   cls:'halfday'},
    ];
    container.innerHTML = items.map(a => `
        <div class="att-item">
            <div class="att-dot ${a.cls}"></div>
            <div class="att-info">
                <span class="att-label">${a.label}</span>
                <span class="att-count">${attData[a.key] || 0}</span>
            </div>
        </div>`).join('');
}

// ── Employees ─────────────────────────────────────────
async function loadEmployees() {
    try {
        const employees = await api('/api/employees');
        employeeCache = employees;
        const tbody  = document.getElementById('empTableBody');
        const countEl = document.getElementById('empRecordCount');
        if (countEl) countEl.textContent = employees.length + ' records';
        const adminRoles = ['manager','director','vp','cxo'];
        const isAdmin    = adminRoles.includes(currentUser?.role);

        if (!employees.length) {
            tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><div class="empty-icon">👥</div><p>No employees yet</p></div></td></tr>`;
            return;
        }

        const statusBadge = (s) => {
            const map = { active:'badge-green', on_leave:'badge-amber', terminated:'badge-red', probation:'badge-gray' };
            return `<span class="badge ${map[s]||'badge-gray'}">${s.replace(/_/g,' ')}</span>`;
        };
        const roleBadge = (r) => `<span class="badge badge-ink">${r}</span>`;
        const deptBadge = (d) => `<span class="badge badge-blue">${d}</span>`;

        tbody.innerHTML = employees.map(e => `
            <tr>
                <td class="td-id">${e.id}</td>
                <td class="td-name">${e.name}</td>
                <td class="td-mono" style="color:var(--ink-3);">${e.email}</td>
                <td>${deptBadge(e.department)}</td>
                <td style="color:var(--ink-3);font-size:12px;">${e.position || '—'}</td>
                <td>${roleBadge(e.role)}</td>
                <td>${statusBadge(e.status)}</td>
                <td>
                    ${isAdmin ? `
                    <button onclick="openEditEmployee(${e.id})" class="btn-action" title="Edit">✏</button>
                    <button onclick="deleteEmployee(${e.id},'${e.name.replace(/'/g,"\\'")}') " class="btn-action btn-danger" title="Delete">✕</button>
                    ` : ''}
                </td>
            </tr>`).join('');
    } catch(e) { console.error('Employees:', e); }
}

// ── Attendance ────────────────────────────────────────
async function loadAttendance() {
    try {
        const dateFrom = document.getElementById('attDateFrom')?.value;
        const dateTo   = document.getElementById('attDateTo')?.value;
        let url = '/api/attendance?page_size=100';
        if (dateFrom) url += `&date_from=${dateFrom}`;
        if (dateTo)   url += `&date_to=${dateTo}`;

        const records  = await api(url);
        const tbody    = document.getElementById('attTableBody');
        const countEl  = document.getElementById('attRecordCount');
        if (countEl) countEl.textContent = records.length + ' records';

        if (!records.length) {
            tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">📋</div><p>No records for this period</p></div></td></tr>`;
            return;
        }

        const statusBadge = (s) => {
            const map = { present:'badge-green', work_from_home:'badge-blue', late:'badge-amber', absent:'badge-red', half_day:'badge-gray' };
            return `<span class="badge ${map[s]||'badge-gray'}">${s.replace(/_/g,' ')}</span>`;
        };

        tbody.innerHTML = records.map(a => `
            <tr>
                <td class="td-id">${a.id}</td>
                <td class="td-name">${a.employee_name}</td>
                <td class="td-mono" style="color:var(--ink-3);">${formatDate(a.date)}</td>
                <td>${statusBadge(a.status)}</td>
                <td class="td-mono" style="color:var(--ink-3);">${a.check_in || '—'}</td>
                <td class="td-mono" style="color:var(--ink-3);">${a.check_out || '—'}</td>
            </tr>`).join('');
    } catch(e) { console.error('Attendance:', e); }
}

// ── Leaves ────────────────────────────────────────────
async function loadLeaves() {
    try {
        const leaves  = await api('/api/leaves?page_size=100');
        const tbody   = document.getElementById('leaveTableBody');
        const countEl = document.getElementById('leaveRecordCount');
        if (countEl) countEl.textContent = leaves.length + ' records';
        const isAdmin = ['manager','director','vp','cxo'].includes(currentUser?.role);

        const statusBadge = (s) => {
            const map = { pending:'badge-amber', approved:'badge-green', rejected:'badge-red', cancelled:'badge-gray' };
            return `<span class="badge ${map[s]||'badge-gray'}">${s}</span>`;
        };

        if (!leaves.length) {
            tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><div class="empty-icon">🏖️</div><p>No leave requests</p></div></td></tr>`;
            return;
        }

        tbody.innerHTML = leaves.map(l => `
            <tr>
                <td class="td-id">${l.id}</td>
                <td class="td-name">${l.employee_name}</td>
                <td><span class="badge badge-blue">${l.leave_type}</span></td>
                <td class="td-mono" style="color:var(--ink-3);">${formatDate(l.start_date)}</td>
                <td class="td-mono" style="color:var(--ink-3);">${formatDate(l.end_date)}</td>
                <td style="color:var(--ink-3);font-size:12px;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${l.reason||'—'}</td>
                <td>${statusBadge(l.status)}</td>
                <td>
                    ${isAdmin && l.status === 'pending' ? `
                    <button onclick="updateLeave(${l.id},'approved')" class="btn-action" title="Approve">✓</button>
                    <button onclick="updateLeave(${l.id},'rejected')" class="btn-action btn-danger" title="Reject">✕</button>
                    ` : ''}
                </td>
            </tr>`).join('');
        renderPendingLeaves(leaves);
    } catch(e) { console.error('Leaves:', e); }
}

// ── Employee CRUD ─────────────────────────────────────
let editingEmpId = null;

function openModal(id) {
    document.getElementById(id).style.display = 'flex';
    if (id === 'leaveModal') populateLeaveEmployees();
}

function closeModal(id) {
    document.getElementById(id).style.display = 'none';
    if (id === 'empModal') {
        editingEmpId = null;
        document.getElementById('empModalTitle').textContent = 'Add employee';
        ['empName','empEmail','empPhone','empPosition','empSalary','empPassword'].forEach(f => {
            const el = document.getElementById(f); if (el) el.value = '';
        });
        const deptEl = document.getElementById('empDepartment');
        const roleEl = document.getElementById('empRole');
        if (deptEl) deptEl.value = '';
        if (roleEl) roleEl.value = 'mid';
        const errEl = document.getElementById('empModalError');
        if (errEl) errEl.style.display = 'none';
    }
}

function closeModalOnBackdrop(e, id) {
    if (e.target.id === id) closeModal(id);
}

function openEditEmployee(empId) {
    const emp = employeeCache.find(e => e.id === empId);
    if (!emp) return;
    editingEmpId = empId;
    document.getElementById('empModalTitle').textContent = 'Edit employee';
    document.getElementById('empName').value       = emp.name;
    document.getElementById('empEmail').value      = emp.email;
    document.getElementById('empPhone').value      = emp.phone || '';
    document.getElementById('empPosition').value   = emp.position || '';
    document.getElementById('empDepartment').value = emp.department;
    document.getElementById('empRole').value       = emp.role;
    document.getElementById('empSalary').value     = emp.salary || '';
    document.getElementById('empPassword').value   = '';
    openModal('empModal');
}

async function saveEmployee() {
    const name       = document.getElementById('empName').value.trim();
    const email      = document.getElementById('empEmail').value.trim();
    const department = document.getElementById('empDepartment').value;
    const errorEl    = document.getElementById('empModalError');
    const btn        = document.getElementById('saveEmpBtn');

    if (!name || !email || !department) {
        errorEl.textContent = 'Name, email and department are required.';
        errorEl.style.display = 'block'; return;
    }
    const body = {
        name, email,
        phone:    document.getElementById('empPhone').value.trim(),
        position: document.getElementById('empPosition').value.trim(),
        department,
        role:     document.getElementById('empRole').value,
        salary:   parseFloat(document.getElementById('empSalary').value) || 0,
        password: document.getElementById('empPassword').value || undefined,
    };
    try {
        errorEl.style.display = 'none';
        btn.disabled = true; btn.textContent = 'Saving…';
        if (editingEmpId) {
            await api(`/api/employees/${editingEmpId}`, { method:'PUT', body:JSON.stringify(body) });
        } else {
            await api('/api/employees', { method:'POST', body:JSON.stringify(body) });
        }
        closeModal('empModal');
        await Promise.all([loadEmployees(), loadStats()]);
    } catch(err) {
        errorEl.textContent = err.message; errorEl.style.display = 'block';
    } finally {
        btn.disabled = false; btn.textContent = 'Save employee';
    }
}

async function deleteEmployee(empId, empName) {
    if (!confirm(`Delete ${empName}? This cannot be undone.`)) return;
    try {
        await api(`/api/employees/${empId}`, { method:'DELETE' });
        await Promise.all([loadEmployees(), loadStats()]);
    } catch(err) { alert('Failed: ' + err.message); }
}

// ── Leave CRUD ────────────────────────────────────────
function populateLeaveEmployees() {
    const sel = document.getElementById('leaveEmpId');
    sel.innerHTML = employeeCache.length
        ? employeeCache.map(e => `<option value="${e.id}">${e.name}</option>`).join('')
        : '<option value="">No employees found</option>';
}

async function saveLeave() {
    const empId   = parseInt(document.getElementById('leaveEmpId').value);
    const start   = document.getElementById('leaveStart').value;
    const end     = document.getElementById('leaveEnd').value;
    const errorEl = document.getElementById('leaveModalError');
    const btn     = document.getElementById('saveLeaveBtn');

    if (!empId || !start || !end) {
        errorEl.textContent = 'Employee, start date and end date are required.';
        errorEl.style.display = 'block'; return;
    }
    if (end < start) {
        errorEl.textContent = 'End date must be on or after start date.';
        errorEl.style.display = 'block'; return;
    }
    try {
        errorEl.style.display = 'none';
        btn.disabled = true; btn.textContent = 'Submitting…';
        await api('/api/leaves', {
            method:'POST',
            body: JSON.stringify({
                employee_id: empId,
                leave_type:  document.getElementById('leaveType').value,
                start_date:  start, end_date: end,
                reason:      document.getElementById('leaveReason').value.trim(),
            }),
        });
        closeModal('leaveModal');
        await Promise.all([loadLeaves(), loadStats()]);
    } catch(err) {
        errorEl.textContent = err.message; errorEl.style.display = 'block';
    } finally {
        btn.disabled = false; btn.textContent = 'Submit request';
    }
}

async function updateLeave(leaveId, status) {
    const label = status === 'approved' ? 'Approve' : 'Reject';
    if (!confirm(`${label} this leave request?`)) return;
    try {
        await api(`/api/leaves/${leaveId}`, { method:'PUT', body:JSON.stringify({ status }) });
        await Promise.all([loadLeaves(), loadStats()]);
    } catch(err) { alert('Failed: ' + err.message); }
}

function renderPendingLeaves(leaves) {
    const container = document.getElementById('dashPendingLeaves');
    if (!container) return;
    const pending = leaves.filter(l => l.status === 'pending').slice(0, 5);
    if (!pending.length) {
        container.innerHTML = `<div class="dash-leave-empty">No pending requests 🎉</div>`;
        return;
    }
    container.innerHTML = pending.map(l => {
        const initials = l.employee_name.split(' ').map(p => p[0]).join('').toUpperCase().slice(0,2);
        const days = Math.ceil((new Date(l.end_date) - new Date(l.start_date)) / 86400000) + 1;
        return `
        <div class="dash-leave-item">
            <div class="dash-leave-avatar">${initials}</div>
            <div class="dash-leave-info">
                <div class="dash-leave-name">${l.employee_name}</div>
                <div class="dash-leave-meta">${l.leave_type} · ${days}d from ${formatDate(l.start_date)}</div>
            </div>
            <span class="dash-leave-badge">pending</span>
        </div>`;
    }).join('');
}

// ── Navigation ────────────────────────────────────────
const pageTitles = { dashboard:'Dashboard', employees:'Employees', attendance:'Attendance', leaves:'Leave Requests', schema:'Schema Info' };

function switchTab(tabName) {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.tab === tabName);
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `tab-${tabName}`);
    });
    const pageEl = document.getElementById('topbarPage');
    if (pageEl) pageEl.textContent = pageTitles[tabName] || tabName;
    document.getElementById('sidebar').classList.remove('mobile-open');
}

function toggleMobileSidebar() {
    document.getElementById('sidebar').classList.toggle('mobile-open');
}

// ── Utils ─────────────────────────────────────────────
function formatDate(iso) {
    const d = new Date(iso + (iso.length === 10 ? 'T00:00:00' : ''));
    return d.toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' });
}

// ── Register / Login Screen Toggle ────────────────────

function showRegister() {
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('registerScreen').style.display = 'flex';
}

function showLogin() {
    document.getElementById('registerScreen').style.display = 'none';
    document.getElementById('loginScreen').style.display = 'flex';
}

function autoSlug() {
    const name = document.getElementById('regOrgName').value;
    const slug = name.toLowerCase().trim()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-');
    document.getElementById('regSlug').value = slug;
}

async function handleRegister(event) {
    event.preventDefault();
    const btn = document.getElementById('registerBtn');
    const errEl = document.getElementById('registerError');
    errEl.style.display = 'none';
    btn.disabled = true;
    btn.textContent = 'Creating workspace...';

    try {
        const res = await fetch('/api/organizations/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                org_name: document.getElementById('regOrgName').value,
                org_slug: document.getElementById('regSlug').value,
                admin_name: document.getElementById('regName').value,
                email: document.getElementById('regEmail').value,
                password: document.getElementById('regPassword').value,
            })
        });

        const data = await res.json();

        if (!res.ok) {
            errEl.textContent = data.detail || 'Registration failed';
            errEl.style.display = 'block';
            return;
        }

        // Store token and log them straight in
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('orgId', data.org_id);
        localStorage.setItem('orgName', data.org_name);
        localStorage.setItem('employeeName', data.employee_name);
        localStorage.setItem('employeeRole', data.employee_role);

        document.getElementById('registerScreen').style.display = 'none';
        await initDashboard();

    } catch (err) {
        errEl.textContent = 'Network error — please try again';
        errEl.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Create workspace →';
    }
}

// Register / Login Screen Toggle
function showRegister() {
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('registerScreen').style.display = 'flex';
}

function showLogin() {
    document.getElementById('registerScreen').style.display = 'none';
    document.getElementById('loginScreen').style.display = 'flex';
}

function autoSlug() {
    const name = document.getElementById('regOrgName').value;
    const slug = name.toLowerCase().trim()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-');
    document.getElementById('regSlug').value = slug;
}

async function handleRegister(event) {
    event.preventDefault();
    const btn = document.getElementById('registerBtn');
    const errEl = document.getElementById('registerError');
    errEl.style.display = 'none';
    btn.disabled = true;
    btn.textContent = 'Creating workspace...';

    try {
        const res = await fetch('/api/organizations/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                org_name: document.getElementById('regOrgName').value,
                org_slug: document.getElementById('regSlug').value,
                admin_name: document.getElementById('regName').value,
                email: document.getElementById('regEmail').value,
                password: document.getElementById('regPassword').value,
            })
        });

        const data = await res.json();

        if (!res.ok) {
            errEl.textContent = data.detail || 'Registration failed';
            errEl.style.display = 'block';
            return;
        }

        localStorage.setItem('token', data.access_token);
        localStorage.setItem('orgId', data.org_id);
        localStorage.setItem('orgName', data.org_name);
        localStorage.setItem('employeeName', data.employee_name);
        localStorage.setItem('employeeRole', data.employee_role);

        document.getElementById('registerScreen').style.display = 'none';
        await initDashboard();

    } catch (err) {
        errEl.textContent = 'Network error — please try again';
        errEl.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Create workspace';
    }
}
