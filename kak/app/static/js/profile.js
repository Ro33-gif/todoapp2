document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const userEmail = document.getElementById('userEmail');
    const userRole = document.getElementById('userRole');
    const profileError = document.getElementById('profile-error');
    
    // Task statistics elements
    const totalUserTasks = document.getElementById('total-user-tasks');
    const pendingUserTasks = document.getElementById('pending-user-tasks');
    const completedUserTasks = document.getElementById('completed-user-tasks');
    
    // Task history elements
    const taskHistoryList = document.getElementById('task-history-list');
    const noHistory = document.getElementById('no-history');
    const historyFilter = document.getElementById('historyFilter');
    const searchHistory = document.getElementById('searchHistory');
    
    // Store data
    let user = null;
    let tasks = [];
    let categoryChart = null;
    
    // Initialize
    init();
    
    async function init() {
        // Check if user is authenticated
        user = await getCurrentUser();
        if (!user) {
            window.location.href = '/';
            return;
        }
        
        // Display user info
        displayUserInfo();
        
        // Load data
        loadTaskStatistics();
        loadTaskHistory();
        
        // Add event listeners
        setupEventListeners();
    }
    
    function setupEventListeners() {
        // Task history filters
        historyFilter?.addEventListener('change', filterTaskHistory);
        searchHistory?.addEventListener('input', filterTaskHistory);
    }
    
    // Display user information
    function displayUserInfo() {
        if (!user) return;
        
        userEmail.value = user.email || '';
        userRole.value = user.is_admin ? 'Admin' : 'User';
    }
    
    // Load task statistics
    async function loadTaskStatistics() {
        try {
            // Get tasks from API
            const response = await fetch('/tasks/');
            
            if (!response.ok) {
                throw new Error('Failed to load tasks');
            }
            
            tasks = await response.json();
            
            // Calculate statistics
            const total = tasks.length;
            const completed = tasks.filter(task => task.status === 'completed').length;
            const pending = total - completed;
            
            // Update DOM
            totalUserTasks.textContent = total;
            completedUserTasks.textContent = completed;
            pendingUserTasks.textContent = pending;
            
            // Create category distribution chart
            createCategoryChart(tasks);
        } catch (error) {
            console.error('Error loading task statistics:', error);
            showAlert(`Error loading task statistics: ${error.message}`, 'danger');
        }
    }
    
    // Create category distribution chart
    function createCategoryChart(tasks) {
        // Count tasks by category
        const categoryData = {};
        
        tasks.forEach(task => {
            const category = task.category || 'other';
            categoryData[category] = (categoryData[category] || 0) + 1;
        });
        
        // Prepare data for chart
        const labels = Object.keys(categoryData);
        const data = Object.values(categoryData);
        const backgroundColors = generateColors(labels.length);
        
        // Create chart
        const ctx = document.getElementById('category-chart');
        
        if (!ctx) return;
        
        // Destroy existing chart if exists
        if (categoryChart) {
            categoryChart.destroy();
        }
        
        // Create new chart
        categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: backgroundColors,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Generate random colors for chart
    function generateColors(count) {
        const colors = [
            '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
            '#5a5c69', '#6f42c1', '#fd7e14', '#20c9a6', '#6610f2'
        ];
        
        // If we need more colors than we have defined, generate random ones
        if (count > colors.length) {
            for (let i = colors.length; i < count; i++) {
                const r = Math.floor(Math.random() * 200);
                const g = Math.floor(Math.random() * 200);
                const b = Math.floor(Math.random() * 200);
                colors.push(`rgb(${r}, ${g}, ${b})`);
            }
        }
        
        return colors.slice(0, count);
    }
    
    // Load task history
    async function loadTaskHistory() {
        try {
            // We already have tasks from loadTaskStatistics, just re-use the data
            if (tasks.length === 0) {
                const response = await fetch('/tasks/');
                
                if (!response.ok) {
                    throw new Error('Failed to load tasks');
                }
                
                tasks = await response.json();
            }
            
            // Sort tasks by creation date (newest first)
            tasks.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
            
            // Render task history
            renderTaskHistory(tasks);
        } catch (error) {
            console.error('Error loading task history:', error);
            showAlert(`Error loading task history: ${error.message}`, 'danger');
        }
    }
    
    // Render task history
    function renderTaskHistory(filteredTasks = null) {
        const tasksToRender = filteredTasks || tasks;
        
        if (tasksToRender.length === 0) {
            taskHistoryList.innerHTML = '';
            noHistory.classList.remove('d-none');
            return;
        }
        
        noHistory.classList.add('d-none');
        
        let html = '';
        tasksToRender.forEach(task => {
            const createdAt = new Date(task.createdAt).toLocaleString();
            const statusBadge = task.status === 'completed' 
                ? '<span class="badge bg-success">Completed</span>' 
                : '<span class="badge bg-warning text-dark">Pending</span>';
            const categoryBadge = task.category 
                ? `<span class="badge bg-info me-2">${task.category}</span>` 
                : '';
            
            html += `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <div class="fw-bold">${task.title}</div>
                        <div class="small text-muted">${createdAt}</div>
                    </div>
                    <div>
                        ${categoryBadge}
                        ${statusBadge}
                    </div>
                </li>
            `;
        });
        
        taskHistoryList.innerHTML = html;
    }
    
    // Filter task history
    function filterTaskHistory() {
        const searchTerm = searchHistory?.value.toLowerCase().trim() || '';
        const statusFilter = historyFilter?.value || 'all';
        
        let filteredTasks = [...tasks];
        
        // Apply status filter
        if (statusFilter === 'completed') {
            filteredTasks = filteredTasks.filter(task => task.status === 'completed');
        } else if (statusFilter === 'pending') {
            filteredTasks = filteredTasks.filter(task => task.status === 'pending');
        }
        
        // Apply search filter
        if (searchTerm) {
            filteredTasks = filteredTasks.filter(task => 
                task.title.toLowerCase().includes(searchTerm) || 
                (task.description && task.description.toLowerCase().includes(searchTerm)) ||
                (task.category && task.category.toLowerCase().includes(searchTerm))
            );
        }
        
        renderTaskHistory(filteredTasks);
    }
    
    // Helper: Show alert message
    function showAlert(message, type = 'danger') {
        // Create alert element
        const alertEl = document.createElement('div');
        alertEl.className = `alert alert-${type} alert-dismissible fade show`;
        alertEl.role = 'alert';
        alertEl.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Add to page
        profileError.innerHTML = '';
        profileError.appendChild(alertEl);
        profileError.classList.remove('d-none');
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertEl.remove();
            if (profileError.childElementCount === 0) {
                profileError.classList.add('d-none');
            }
        }, 5000);
    }
}); 