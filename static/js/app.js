/* ═══════════════════════════════════════════════════════════════════════════
   HR SaaS — app.js
   Auth state in JS variables only. No localStorage.
   ═══════════════════════════════════════════════════════════════════════════ */

// ── Auth State (memory only) ──────────────────────────────────────────────
let authToken = null;
let currentOrgId = null;
let currentUser = null;
let employeeCache = [];

const API = '';
const ADMIN_ROLES = new Set(['manager', 'director', 'vp', 'cxo']);

// ── Helpers ───────────────────────────────────────────────────────────────

function headers() {
    const h = { 'Content-Type': 'application/json' };
    if (authToken) h['Authorization'] = `Bearer ${authToken}`;
    if (currentOrgId) h['X-Org-Id'] = String(currentOrgId);
    return h;
}

async function api(endpoint, options = {}) {
    const res = await fetch(`${API}${endpoint}`, {
        headers: headers(),
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(err.detail || `HTTP ${res.status}`);
    }
    if (res.status === 204) return null;
    return res.json();
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

function getInitials(name) {
    if (!name) return '?';
    return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatCurrency(amount) {
    if (!amount && amount !== 0) return '-';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(amount);
}

function getBadgeClass(status) {
    const map = {
        active: 'badge-success', present: 'badge-success', approved: 'badge-success',
        on_leave: 'badge-warning', pending: 'badge-warning', late: 'badge-warning', half_day: 'badge-warning',
        terminated: 'badge-danger', absent: 'badge-danger', rejected: 'badge-danger',
        work_from_home: 'badge-info', probation: 'badge-info', cancelled: 'badge-neutral',
    };
    return map[status] || 'badge-neutral';
}

function getStatusLabel(status) {
    return (status || '').replace(/_/g, ' ');
}

function isAdmin() {
    return currentUser && ADMIN_ROLES.has(currentUser.role);
}

// ── Screen Management ─────────────────────────────────────────────────────

function showScreen(screenId) {
    document.querySelectorAll('.auth-wrapper, .dashboard').forEach(el => el.classList.add('hidden'));
    const el = document.getElementById(screenId);
    if (el) el.classList.remove('hidden');
}

function showLoginScreen() {
    showScreen('loginScreen');
}

function showRegisterScreen() {
    showScreen('registerScreen');
}

function showDashboard() {
    showScreen('dashboardScreen');

    // Populate user info
    if (currentUser) {
        document.getElementById('sidebarOrgName').textContent = currentUser.org_name || '';
        document.getElementById('sidebarUserName').textContent = currentUser.name || '';
        document.getElementById('sidebarUserRole').textContent = currentUser.role || '';
        document.getElementById('sidebarAvatar').textContent = getInitials(currentUser.name);
        document.getElementById('topbarName').textContent = currentUser.name || '';
        document.getElementById('topbarAvatar').textContent = getInitials(currentUser.name);
    }

    // Show/hide admin controls
    const addEmpBtn = document.getElementById('addEmpBtn');
    if (addEmpBtn) {
        addEmpBtn.classList.toggle('hidden', !isAdmin());
    }

    switchTab('dashboard');
    loadAllData();
}

// ── Tab Switching ─────────────────────────────────────────────────────────

function switchTab(tab) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

    const tabEl = document.getElementById(`tab-${tab}`);
    if (tabEl) tabEl.classList.add('active');

    const navEl = document.querySelector(`[data-tab="${tab}"]`);
    if (navEl) navEl.classList.add('active');

    // Update page title
    const titles = {
        dashboard: 'Dashboard',
        employees: 'Employees',
        attendance: 'Attendance',
        leaves: 'Leave Requests',
        schema: 'Schema Info'
    };
    document.getElementById('pageTitle').textContent = titles[tab] || 'Dashboard';
}

// ── Auth ──────────────────────────────────────────────────────────────────

function fillLogin(email) {
    document.getElementById('loginEmail').value = email;
    document.getElementById('loginPassword').value = 'password123';
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const data = await api('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
        authToken = data.access_token;
        currentUser = data.employee;
        currentOrgId = data.employee.org_id;
        showDashboard();
        showToast(`Welcome back, ${currentUser.name}!`, 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const name = document.getElementById('regCompanyName').value;
    const slug = document.getElementById('regSlug').value;
    const adminName = document.getElementById('regAdminName').value;
    const adminEmail = document.getElementById('regAdminEmail').value;
    const adminPassword = document.getElementById('regAdminPassword').value;

    try {
        const data = await api('/api/organizations/register', {
            method: 'POST',
            body: JSON.stringify({
                name, slug,
                admin_name: adminName,
                admin_email: adminEmail,
                admin_password: adminPassword,
            }),
        });
        authToken = data.access_token;
        currentUser = data.employee;
        currentOrgId = data.employee.org_id;
        showDashboard();
        showToast('Organization registered successfully!', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function handleLogout() {
    authToken = null;
    currentUser = null;
    currentOrgId = null;
    employeeCache = [];
    showLoginScreen();
    showToast('Logged out', 'info');
}

function showForgotScreen() {
    showScreen('forgotScreen');
}

function showResetScreen() {
    showScreen('resetScreen');
}

async function handleForgotPassword(e) {
    e.preventDefault();
    const email = document.getElementById('forgotEmail').value;
    try {
        const data = await api('/api/auth/forgot-password', {
            method: 'POST',
            body: JSON.stringify({ email }),
        });
        showToast(data.message || 'If that email exists, a reset link was sent.', 'success');
        // Move user to reset screen so they can paste the token
        document.getElementById('forgotForm').reset();
        showResetScreen();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function handleResetPassword(e) {
    e.preventDefault();
    const token = document.getElementById('resetToken').value.trim();
    const newPassword = document.getElementById('resetNewPassword').value;
    const confirmPassword = document.getElementById('resetConfirmPassword').value;

    if (newPassword !== confirmPassword) {
        showToast('Passwords do not match', 'error');
        return;
    }

    try {
        const data = await api('/api/auth/reset-password', {
            method: 'POST',
            body: JSON.stringify({ token, new_password: newPassword }),
        });
        showToast(data.message || 'Password reset successfully. Please sign in.', 'success');
        document.getElementById('resetForm').reset();
        showLoginScreen();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ── Data Loading ──────────────────────────────────────────────────────────

async function loadAllData() {
    await Promise.all([
        loadStats(),
        loadEmployees(),
        loadAttendance(),
        loadLeaves(),
    ]);
}

// ── Stats / Dashboard ─────────────────────────────────────────────────────

async function loadStats() {
    try {
        const stats = await api('/api/stats');
        renderKPIs(stats);
        renderDeptChart(stats.departments || {});
        renderTodayAttendance(stats.today_attendance_list || []);
        renderPendingLeaves(stats.pending_leaves_list || []);
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

function renderKPIs(stats) {
    document.getElementById('kpiTotalEmployees').textContent = stats.total_employees || 0;
    document.getElementById('kpiActiveEmployees').textContent = stats.active_employees || 0;
    document.getElementById('kpiPendingLeaves').textContent = stats.pending_leaves || 0;
    document.getElementById('kpiAvgSalary').textContent = formatCurrency(stats.avg_salary);

    const todayAtt = stats.today_attendance || {};
    const presentCount = (todayAtt.present || 0) + (todayAtt.work_from_home || 0) + (todayAtt.late || 0);
    document.getElementById('kpiPresentToday').textContent = presentCount;
}

function renderDeptChart(departments) {
    const container = document.getElementById('deptChart');
    if (!container) return;

    const entries = Object.entries(departments);
    if (entries.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No department data</p></div>';
        return;
    }

    const maxVal = Math.max(...entries.map(([,v]) => v));
    const colors = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6'];

    container.innerHTML = entries.map(([dept, count], i) => `
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
            <span style="width:90px;font-size:0.82rem;font-weight:600;text-transform:capitalize;color:var(--text-secondary)">${dept}</span>
            <div style="flex:1;background:var(--paper);border-radius:6px;height:26px;overflow:hidden;">
                <div style="width:${(count / maxVal) * 100}%;height:100%;background:${colors[i % colors.length]};border-radius:6px;transition:width 0.5s ease;display:flex;align-items:center;padding-left:8px;">
                    <span style="font-size:0.75rem;font-weight:700;color:white">${count}</span>
                </div>
            </div>
        </div>
    `).join('');
}

function renderTodayAttendance(list) {
    const container = document.getElementById('todayAttendanceGrid');
    if (!container) return;

    if (list.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-icon">📋</div><p>No attendance records for today</p></div>';
        return;
    }

    container.innerHTML = list.map(a => `
        <div class="attendance-chip">
            <span class="chip-dot dot-${a.status}"></span>
            <span>${a.employee_name}</span>
        </div>
    `).join('');
}

function renderPendingLeaves(list) {
    const container = document.getElementById('pendingLeavesList');
    if (!container) return;

    if (list.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-icon">✅</div><p>No pending leave requests</p></div>';
        return;
    }

    container.innerHTML = list.map(l => `
        <div class="leave-item">
            <div class="leave-info">
                <span class="leave-name">${l.employee_name}</span>
                <span class="leave-dates">${l.leave_type} · ${formatDate(l.start_date)} — ${formatDate(l.end_date)}</span>
            </div>
            <span class="badge badge-warning">Pending</span>
        </div>
    `).join('');
}

// ── Employees ─────────────────────────────────────────────────────────────

async function loadEmployees() {
    try {
        const employees = await api('/api/employees');
        employeeCache = employees;
        renderEmployeeTable(employees);
    } catch (err) {
        console.error('Failed to load employees:', err);
    }
}

function filterEmployees() {
    const query = document.getElementById('empSearch')?.value.toLowerCase().trim() || '';
    if (!query) {
        renderEmployeeTable(employeeCache);
        return;
    }
    const filtered = employeeCache.filter(emp =>
        emp.name.toLowerCase().includes(query) ||
        emp.email.toLowerCase().includes(query)
    );
    renderEmployeeTable(filtered);
}

function renderEmployeeTable(employees) {
    const tbody = document.getElementById('employeeTableBody');
    if (!tbody) return;

    if (employees.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No employees found</td></tr>';
        return;
    }

    tbody.innerHTML = employees.map(emp => `
        <tr>
            <td>
                <div style="display:flex;align-items:center;gap:10px">
                    <div class="topbar-avatar">${getInitials(emp.name)}</div>
                    <div>
                        <div style="font-weight:600">${emp.name}</div>
                        <div style="font-size:0.78rem;color:var(--text-secondary)">${emp.email}</div>
                    </div>
                </div>
            </td>
            <td><span class="badge badge-info">${getStatusLabel(emp.department)}</span></td>
            <td>${getStatusLabel(emp.role)}</td>
            <td>${emp.position || '-'}</td>
            <td>${formatCurrency(emp.salary)}</td>
            <td><span class="badge ${getBadgeClass(emp.status)}">${getStatusLabel(emp.status)}</span></td>
            <td>
                ${isAdmin() ? `
                    <button class="btn btn-outline btn-sm" onclick="openEditEmployee(${emp.id})">Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteEmployee(${emp.id})">Del</button>
                ` : ''}
            </td>
        </tr>
    `).join('');
}

function openAddEmployee() {
    document.getElementById('empModalTitle').textContent = 'Add Employee';
    document.getElementById('empForm').reset();
    document.getElementById('empModalId').value = '';
    document.getElementById('empPasswordGroup').classList.remove('hidden');
    document.getElementById('empModal').classList.remove('hidden');
}

function openEditEmployee(id) {
    const emp = employeeCache.find(e => e.id === id);
    if (!emp) return;

    document.getElementById('empModalTitle').textContent = 'Edit Employee';
    document.getElementById('empModalId').value = emp.id;
    document.getElementById('empName').value = emp.name || '';
    document.getElementById('empEmail').value = emp.email || '';
    document.getElementById('empPhone').value = emp.phone || '';
    document.getElementById('empDepartment').value = emp.department || '';
    document.getElementById('empRole').value = emp.role || '';
    document.getElementById('empPosition').value = emp.position || '';
    document.getElementById('empSalary').value = emp.salary || '';
    document.getElementById('empStatus').value = emp.status || 'active';
    document.getElementById('empPasswordGroup').classList.add('hidden');
    document.getElementById('empModal').classList.remove('hidden');
}

async function handleEmployeeSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('empModalId').value;
    const data = {
        name: document.getElementById('empName').value,
        email: document.getElementById('empEmail').value,
        phone: document.getElementById('empPhone').value || null,
        department: document.getElementById('empDepartment').value,
        role: document.getElementById('empRole').value,
        position: document.getElementById('empPosition').value || null,
        salary: parseFloat(document.getElementById('empSalary').value) || null,
        status: document.getElementById('empStatus').value,
    };

    try {
        if (id) {
            await api(`/api/employees/${id}`, { method: 'PUT', body: JSON.stringify(data) });
            showToast('Employee updated', 'success');
        } else {
            data.password = document.getElementById('empPassword').value;
            await api('/api/employees', { method: 'POST', body: JSON.stringify(data) });
            showToast('Employee added', 'success');
        }
        closeModal('empModal');
        await loadEmployees();
        await loadStats();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function deleteEmployee(id) {
    if (!confirm('Delete this employee? This cannot be undone.')) return;
    try {
        await api(`/api/employees/${id}`, { method: 'DELETE' });
        showToast('Employee deleted', 'success');
        await loadEmployees();
        await loadStats();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ── Attendance ────────────────────────────────────────────────────────────

async function loadAttendance() {
    try {
        const startDate = document.getElementById('attStartDate')?.value || '';
        const endDate = document.getElementById('attEndDate')?.value || '';
        let url = '/api/attendance?limit=100';
        if (startDate) url += `&start_date=${startDate}`;
        if (endDate) url += `&end_date=${endDate}`;

        const records = await api(url);
        renderAttendanceTable(records);
    } catch (err) {
        console.error('Failed to load attendance:', err);
    }
}

function renderAttendanceTable(records) {
    const tbody = document.getElementById('attendanceTableBody');
    if (!tbody) return;

    if (records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No attendance records</td></tr>';
        return;
    }

    tbody.innerHTML = records.map(r => `
        <tr>
            <td style="font-weight:600">${r.employee_name || `Emp #${r.employee_id}`}</td>
            <td>${formatDate(r.date)}</td>
            <td><span class="badge ${getBadgeClass(r.status)}">${getStatusLabel(r.status)}</span></td>
            <td>${r.check_in || '-'}</td>
            <td>${r.check_out || '-'}</td>
        </tr>
    `).join('');
}

// ── Leaves ────────────────────────────────────────────────────────────────

async function loadLeaves() {
    try {
        const statusFilter = document.getElementById('leaveStatusFilter')?.value || '';
        let url = '/api/leaves?limit=100';
        if (statusFilter) url += `&status=${statusFilter}`;

        const leaves = await api(url);
        renderLeaveTable(leaves);
    } catch (err) {
        console.error('Failed to load leaves:', err);
    }
}

function renderLeaveTable(leaves) {
    const tbody = document.getElementById('leaveTableBody');
    if (!tbody) return;

    if (leaves.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No leave requests</td></tr>';
        return;
    }

    tbody.innerHTML = leaves.map(l => `
        <tr>
            <td style="font-weight:600">${l.employee_name || `Emp #${l.employee_id}`}</td>
            <td><span class="badge badge-info">${getStatusLabel(l.leave_type)}</span></td>
            <td>${formatDate(l.start_date)}</td>
            <td>${formatDate(l.end_date)}</td>
            <td>${l.reason || '-'}</td>
            <td><span class="badge ${getBadgeClass(l.status)}">${getStatusLabel(l.status)}</span></td>
            <td>
                ${isAdmin() && l.status === 'pending' ? `
                    <button class="btn btn-success btn-sm" onclick="updateLeave(${l.id}, 'approved')">Approve</button>
                    <button class="btn btn-danger btn-sm" onclick="updateLeave(${l.id}, 'rejected')">Reject</button>
                ` : ''}
            </td>
        </tr>
    `).join('');
}

async function updateLeave(id, status) {
    try {
        await api(`/api/leaves/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ status }),
        });
        showToast(`Leave ${status}`, 'success');
        await loadLeaves();
        await loadStats();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function openAddLeave() {
    document.getElementById('leaveForm').reset();
    document.getElementById('leaveModal').classList.remove('hidden');
}

async function handleLeaveSubmit(e) {
    e.preventDefault();
    const data = {
        leave_type: document.getElementById('leaveType').value,
        start_date: document.getElementById('leaveStart').value,
        end_date: document.getElementById('leaveEnd').value,
        reason: document.getElementById('leaveReason').value || null,
    };

    try {
        await api('/api/leaves', { method: 'POST', body: JSON.stringify(data) });
        showToast('Leave request submitted', 'success');
        closeModal('leaveModal');
        await loadLeaves();
        await loadStats();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ── Modal ─────────────────────────────────────────────────────────────────

function closeModal(id) {
    document.getElementById(id).classList.add('hidden');
}

// ── Sidebar Toggle (mobile) ──────────────────────────────────────────────

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
    document.getElementById('sidebarOverlay').classList.toggle('show');
}

// ── Slug Generator ────────────────────────────────────────────────────────

function generateSlug(name) {
    return name.toLowerCase().replace(/[^a-z0-9]+/g, '').replace(/-+/g, '-').replace(/^-|-$/g, '');
}

// ── Init ──────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
    // Login form
    document.getElementById('loginForm').addEventListener('submit', handleLogin);

    // Register form
    document.getElementById('registerForm').addEventListener('submit', handleRegister);

    // Forgot / Reset password forms
    document.getElementById('forgotForm').addEventListener('submit', handleForgotPassword);
    document.getElementById('resetForm').addEventListener('submit', handleResetPassword);

    // Auto-generate slug from company name
    document.getElementById('regCompanyName').addEventListener('input', function () {
        document.getElementById('regSlug').value = generateSlug(this.value);
    });

    // Logout
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);

    // Nav items
    document.querySelectorAll('.nav-item[data-tab]').forEach(item => {
        item.addEventListener('click', function () {
            switchTab(this.dataset.tab);
        });
    });

    // Add Employee button
    const addEmpBtn = document.getElementById('addEmpBtn');
    if (addEmpBtn) {
        addEmpBtn.addEventListener('click', openAddEmployee);
    }

    // Employee search
    document.getElementById('empSearch')?.addEventListener('input', filterEmployees);

    // Employee form
    document.getElementById('empForm').addEventListener('submit', handleEmployeeSubmit);

    // Attendance filters
    document.getElementById('attStartDate')?.addEventListener('change', loadAttendance);
    document.getElementById('attEndDate')?.addEventListener('change', loadAttendance);

    // Leave filter
    document.getElementById('leaveStatusFilter')?.addEventListener('change', loadLeaves);

    // Add Leave button
    const addLeaveBtn = document.getElementById('addLeaveBtn');
    if (addLeaveBtn) {
        addLeaveBtn.addEventListener('click', openAddLeave);
    }

    // Leave form
    document.getElementById('leaveForm').addEventListener('submit', handleLeaveSubmit);

    // Mobile sidebar toggle
    document.getElementById('menuToggle')?.addEventListener('click', toggleSidebar);
    document.getElementById('sidebarOverlay')?.addEventListener('click', toggleSidebar);

    // Show login screen
    showLoginScreen();
});
