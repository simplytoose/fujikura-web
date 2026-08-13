document.addEventListener('DOMContentLoaded', function() {
    console.log('Система обліку аплікаторів - готова');

    initializeTooltips();
    initializePopovers();
    setupAlerts();
    initializeMobileTables();
    initializeDarkMode();
});

function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipElements.forEach(el => {
        new bootstrap.Tooltip(el);
    });
}

function initializePopovers() {
    const popoverElements = document.querySelectorAll('[data-bs-toggle="popover"]');
    popoverElements.forEach(el => {
        new bootstrap.Popover(el);
    });
}

function setupAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

function showConfirmation(title, message, onConfirm) {
    if (confirm(message)) {
        onConfirm();
    }
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    };
    return date.toLocaleDateString('uk-UA', options);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    };
    return date.toLocaleDateString('uk-UA', options);
}

function showSuccess(message) {
    showNotification(message, 'success');
}

function showError(message) {
    showNotification(message, 'danger');
}

function showWarning(message) {
    showNotification(message, 'warning');
}

function showInfo(message) {
    showNotification(message, 'info');
}

function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const mainContent = document.querySelector('.main-content') || document.body;
    mainContent.insertBefore(alertDiv, mainContent.firstChild);

    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}

function validateForm(formSelector) {
    const form = document.querySelector(formSelector);
    if (!form) return false;

    return form.checkValidity() === false ? false : true;
}

function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

function csrfHeaders(extraHeaders = {}) {
    return {
        'X-CSRFToken': getCsrfToken(),
        ...extraHeaders
    };
}

async function fetchData(url, options = {}) {
    try {
        const method = (options.method || 'GET').toUpperCase();
        if (method !== 'GET' && method !== 'HEAD') {
            options.headers = csrfHeaders(options.headers || {});
        }

        const response = await fetch(url, options);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        showError('Помилка при завантаженні даних');
        throw error;
    }
}

async function postData(url, data = {}) {
    return fetchData(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });
}

function filterTable(searchSelector, tableSelector) {
    const searchInput = document.querySelector(searchSelector);
    const table = document.querySelector(tableSelector);

    if (!searchInput || !table) return;

    searchInput.addEventListener('keyup', function() {
        const filter = this.value.toUpperCase();
        const rows = table.querySelectorAll('tbody tr');

        rows.forEach(row => {
            const text = row.textContent.toUpperCase();
            row.style.display = text.includes(filter) ? '' : 'none';
        });
    });
}

function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
    updateThemeToggle();
    // If user is authenticated, persist preference server-side
    try {
        if (window.IS_AUTHENTICATED === true || window.IS_AUTHENTICATED === 'true') {
            const theme = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
            fetch('/auth/set-theme', {
                method: 'POST',
                headers: csrfHeaders({'Content-Type': 'application/json'}),
                body: JSON.stringify({theme: theme})
            }).catch(err => console.warn('Could not persist theme:', err));
        }
    } catch (e) {
        console.warn('Theme persist check failed', e);
    }
}

function initializeDarkMode() {
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
        updateThemeToggle();
    }
}

function updateThemeToggle() {
    const btn = document.getElementById('themeToggle');
    if (!btn) return;
    const enabled = document.body.classList.contains('dark-mode');
    btn.textContent = enabled ? '🌙' : '🌓';
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showSuccess('Скопійовано в буфер обміну');
    }).catch(() => {
        showError('Помилка при копіюванні');
    });
}

function exportTableToCSV(tableSelector, filename = 'export.csv') {
    const table = document.querySelector(tableSelector);
    if (!table) return;

    const csv = [];
    const rows = table.querySelectorAll('tr');

    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const csvCols = [];

        cols.forEach(col => {
            csvCols.push(col.textContent);
        });

        csv.push(csvCols.join(','));
    });

    downloadCSV(csv.join('\n'), filename);
}

function downloadCSV(csv, filename) {
    const link = document.createElement('a');
    link.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
    link.download = filename;
    link.click();
}

function printElement(elementSelector) {
    const element = document.querySelector(elementSelector);
    if (!element) return;

    const printWindow = window.open('', '', 'width=800,height=600');
    printWindow.document.write(element.outerHTML);
    printWindow.document.close();
    printWindow.print();
}

function timeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'щойно';
    if (diffMins < 60) return `${diffMins} хв. тому`;
    if (diffHours < 24) return `${diffHours} год. тому`;
    if (diffDays < 7) return `${diffDays} днів тому`;

    return formatDate(dateString);
}

function setButtonLoading(buttonSelector, loading = true) {
    const button = document.querySelector(buttonSelector);
    if (!button) return;

    if (loading) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Завантаження...';
    } else {
        button.disabled = false;
        button.innerHTML = button.getAttribute('data-original-text') || 'Відправити';
    }
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    const re = /^\+?[\d\s\-\(\)]{10,}$/;
    return re.test(phone);
}

function smoothScrollTo(selector) {
    const element = document.querySelector(selector);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

function initializeMobileTables() {
    document.querySelectorAll('table').forEach(table => {
        const thead = table.querySelector('thead');
        if (!thead) return;

        const headers = Array.from(thead.querySelectorAll('th')).map(th => th.textContent.trim());
        const rows = table.querySelectorAll('tbody tr');

        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            cells.forEach((cell, index) => {
                if (headers[index] && !cell.getAttribute('data-label')) {
                    cell.setAttribute('data-label', headers[index]);
                }
            });
        });
    });
}

console.log('Скрипти завантажені успішно');
