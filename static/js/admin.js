// static/js/admin.js - Admin dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard
    initializeDashboard();
    
    // Initialize charts if Chart.js is available
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
    
    // Initialize data tables
    initializeDataTables();
    
    // Initialize search functionality
    initializeSearch();
});

function initializeDashboard() {
    // Add active class to current nav item
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
    
    // Auto-refresh data every 30 seconds
    setInterval(refreshDashboardData, 30000);
}

function initializeCharts() {
    // Initialize review stats chart
    const reviewChartCanvas = document.getElementById('reviewChart');
    if (reviewChartCanvas) {
        const ctx = reviewChartCanvas.getContext('2d');
        
        // Get data from the page (passed from backend)
        const reviewData = JSON.parse(document.getElementById('review-chart-data').textContent);
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: reviewData.labels,
                datasets: [{
                    label: 'Basic Reviews',
                    data: reviewData.basic,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Advanced Reviews',
                    data: reviewData.advanced,
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Reviews Over Time'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // Initialize payment stats chart
    const paymentChartCanvas = document.getElementById('paymentChart');
    if (paymentChartCanvas) {
        const ctx = paymentChartCanvas.getContext('2d');
        
        const paymentData = JSON.parse(document.getElementById('payment-chart-data').textContent);
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: paymentData.labels,
                datasets: [{
                    label: 'Revenue (₦)',
                    data: paymentData.amounts,
                    backgroundColor: '#27ae60',
                    borderColor: '#229954',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Revenue Over Time'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '₦' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
}

function initializeDataTables() {
    // Add sorting functionality to tables
    const tables = document.querySelectorAll('table');
    
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        
        headers.forEach((header, index) => {
            if (header.textContent.trim() && !header.classList.contains('no-sort')) {
                header.style.cursor = 'pointer';
                header.title = 'Click to sort';
                
                header.addEventListener('click', () => {
                    sortTable(table, index);
                });
            }
        });
    });
}

function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Determine current sort direction
    const header = table.querySelectorAll('th')[columnIndex];
    const isAscending = !header.classList.contains('sort-desc');
    
    // Clear all sort classes
    table.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Add appropriate sort class
    header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
    
    // Sort rows
    rows.sort((a, b) => {
        const aText = a.cells[columnIndex].textContent.trim();
        const bText = b.cells[columnIndex].textContent.trim();
        
        // Try to parse as numbers first
        const aNum = parseFloat(aText.replace(/[^0-9.-]/g, ''));
        const bNum = parseFloat(bText.replace(/[^0-9.-]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? aNum - bNum : bNum - aNum;
        }
        
        // Try to parse as dates
        const aDate = new Date(aText);
        const bDate = new Date(bText);
        
        if (!isNaN(aDate.getTime()) && !isNaN(bDate.getTime())) {
            return isAscending ? aDate - bDate : bDate - aDate;
        }
        
        // Default to string comparison
        return isAscending ? aText.localeCompare(bText) : bText.localeCompare(aText);
    });
    
    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value);
            }, 300);
        });
    }
}

function performSearch(query) {
    const table = document.querySelector('table tbody');
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const matches = text.includes(query.toLowerCase());
        
        row.style.display = matches ? '' : 'none';
    });
}

function refreshDashboardData() {
    // Only refresh on dashboard page
    if (!window.location.pathname.includes('dashboard')) return;
    
    fetch('/admin/dashboard-data')
        .then(response => response.json())
        .then(data => {
            // Update dashboard cards
            updateDashboardCards(data);
        })
        .catch(error => {
            console.error('Error refreshing dashboard data:', error);
        });
}

function updateDashboardCards(data) {
    const cards = {
        'user-count': data.user_count,
        'review-count': data.review_count,
        'payment-count': data.payment_count,
        'payment-total': '₦' + data.payment_total.toLocaleString()
    };
    
    Object.entries(cards).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
}

// Utility functions
function showAlert(message, type = 'info') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    
    const container = document.querySelector('.main');
    container.insertBefore(alert, container.firstChild);
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Export functions for use in templates
window.adminDashboard = {
    showAlert,
    confirmAction,
    refreshDashboardData
};