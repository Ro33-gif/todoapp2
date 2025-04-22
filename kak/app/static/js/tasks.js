document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const tasksContainer = document.getElementById('tasks-container');
    const tasksList = document.getElementById('tasks-list');
    const noTasksMessage = document.getElementById('no-tasks-message');
    const totalTasksCount = document.getElementById('total-tasks');
    const completedTasksCount = document.getElementById('completed-tasks');
    const pendingTasksCount = document.getElementById('pending-tasks');
    const searchInput = document.getElementById('searchTasks');
    
    // Task modal elements
    const taskModal = new bootstrap.Modal(document.getElementById('taskModal'));
    const taskForm = document.getElementById('taskForm');
    const taskId = document.getElementById('taskId');
    const taskTitle = document.getElementById('taskTitle');
    const taskDescription = document.getElementById('taskDescription');
    const taskStatus = document.getElementById('taskStatus');
    const taskImage = document.getElementById('taskImage');
    const currentImageContainer = document.getElementById('currentImageContainer');
    const currentTaskImage = document.getElementById('currentTaskImage');
    const removeTaskImage = document.getElementById('removeTaskImage');
    const saveTaskBtn = document.getElementById('saveTask');
    const taskError = document.getElementById('taskError');
    const taskCategory = document.getElementById('taskCategory');
    const taskUrgency = document.getElementById('taskUrgency');
    const taskDueDate = document.getElementById('taskDueDate');
    
    // Delete confirmation modal
    const deleteTaskModal = new bootstrap.Modal(document.getElementById('deleteTaskModal'));
    const deleteTaskId = document.getElementById('deleteTaskId');
    const confirmDeleteTaskBtn = document.getElementById('confirmDeleteTask');
    
    // Store tasks data
    let tasks = [];
    let originalTaskImageUrl = null;
    let shouldRemoveImage = false;
    
    // Initialize
    init();
    
    // Initialize the tasks page
    async function init() {
        // Check if user is authenticated
        const user = await getCurrentUser();
        if (!user) {
            return;
        }
        
        // Load tasks
        loadTasks();
        
        // Add event listeners for status filter buttons
        document.querySelectorAll('[data-filter]').forEach(button => {
            button.addEventListener('click', function() {
                const filter = this.getAttribute('data-filter');
                
                // Update active button
                document.querySelectorAll('[data-filter]').forEach(btn => {
                    btn.classList.remove('active');
                });
                this.classList.add('active');
                
                // Apply filters
                applyFilters();
            });
        });
        
        // Add event listener for category filter
        const categoryFilter = document.getElementById('categoryFilter');
        if (categoryFilter) {
            categoryFilter.addEventListener('change', function() {
                applyFilters();
            });
        }
        
        // Add event listener for urgency filter
        const urgencyFilter = document.getElementById('urgencyFilter');
        if (urgencyFilter) {
            urgencyFilter.addEventListener('change', function() {
                applyFilters();
            });
        }
        
        // Search functionality
        searchInput?.addEventListener('input', function() {
            applyFilters();
        });
    }
    
    // Get currently active status filter
    function getActiveStatusFilter() {
        const activeFilter = document.querySelector('[data-filter].active');
        return activeFilter ? activeFilter.getAttribute('data-filter') : 'all';
    }
    
    // Get currently selected category filter
    function getActiveCategoryFilter() {
        const categoryFilter = document.getElementById('categoryFilter');
        return categoryFilter ? categoryFilter.value : 'all';
    }
    
    // Get the currently selected urgency filter
    function getActiveUrgencyFilter() {
        const urgencyFilter = document.getElementById('urgencyFilter');
        return urgencyFilter ? urgencyFilter.value : 'all';
    }
    
    // Apply all filters (status, category, urgency, search)
    function applyFilters() {
        const statusFilter = getActiveStatusFilter();
        const categoryFilter = getActiveCategoryFilter();
        const urgencyFilter = getActiveUrgencyFilter();
        const searchTerm = searchInput?.value.toLowerCase().trim() || '';
        
        filterTasks(statusFilter, categoryFilter, urgencyFilter, searchTerm);
    }
    
    // Filter tasks based on status, category, urgency and search term
    function filterTasks(statusFilter = 'all', categoryFilter = 'all', urgencyFilter = 'all', searchTerm = '') {
        let filteredTasks = [...tasks];
        
        // Apply status filter
        if (statusFilter === 'pending') {
            filteredTasks = filteredTasks.filter(task => task.status === 'pending');
        } else if (statusFilter === 'completed') {
            filteredTasks = filteredTasks.filter(task => task.status === 'completed');
        }
        
        // Apply category filter
        if (categoryFilter !== 'all') {
            filteredTasks = filteredTasks.filter(task => task.category === categoryFilter);
        }
        
        // Apply urgency filter
        if (urgencyFilter !== 'all') {
            filteredTasks = filteredTasks.filter(task => task.urgency === urgencyFilter);
        }
        
        // Apply search filter if search term exists
        if (searchTerm) {
            filteredTasks = filteredTasks.filter(task => 
                task.title.toLowerCase().includes(searchTerm) || 
                (task.description && task.description.toLowerCase().includes(searchTerm))
            );
        }
        
        renderTasks(filteredTasks);
    }
    
    // Load tasks from API
    async function loadTasks() {
        try {
            // Show loading state
            tasksList.innerHTML = '<div class="spinner-container"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
            
            const response = await fetch('/tasks/');
            
            if (!response.ok) {
                throw new Error('Failed to load tasks');
            }
            
            tasks = await response.json();
            
            // Update counts
            updateTaskCounts();
            
            // Render tasks
            renderTasks();
        } catch (error) {
            console.error('Error loading tasks:', error);
            tasksList.innerHTML = `<div class="alert alert-danger">Error loading tasks: ${error.message}</div>`;
        }
    }
    
    // Render tasks to the UI
    function renderTasks(filteredTasks = null) {
        const tasksToRender = filteredTasks || tasks;
        
        if (tasksToRender.length === 0) {
            tasksList.innerHTML = '';
            noTasksMessage.classList.remove('d-none');
            return;
        }
        
        noTasksMessage.classList.add('d-none');
        
        let html = '';
        tasksToRender.forEach(task => {
            const statusClass = task.status === 'completed' ? 'completed' : '';
            const statusBadge = task.status === 'completed' 
                ? '<span class="badge bg-success">Completed</span>' 
                : '<span class="badge bg-warning text-dark">Pending</span>';
            
            // Create category badge
            const categoryBadge = task.category 
                ? `<span class="badge bg-info me-2">${task.category}</span>` 
                : '';
                
            // Create urgency badge with appropriate color
            let urgencyClass = 'bg-secondary';
            if (task.urgency === 'high') {
                urgencyClass = 'bg-danger';
            } else if (task.urgency === 'medium') {
                urgencyClass = 'bg-warning text-dark';
            } else if (task.urgency === 'low') {
                urgencyClass = 'bg-info';
            }
            
            const urgencyBadge = task.urgency 
                ? `<span class="badge ${urgencyClass} me-2">Priority: ${task.urgency}</span>` 
                : '';
                
            // Format due date if it exists
            let dueDateHtml = '';
            if (task.dueDate) {
                const dueDate = new Date(task.dueDate);
                const formattedDate = dueDate.toLocaleDateString();
                dueDateHtml = `<p class="card-text text-muted mt-2"><small>Due date: ${formattedDate}</small></p>`;
            }
            
            html += `
                <div class="card task-card ${statusClass}" data-id="${task.id}">
                    <div class="card-header">
                        <h5 class="card-title mb-0">${task.title}</h5>
                        <div class="task-status">
                            ${categoryBadge}
                            ${urgencyBadge}
                            ${statusBadge}
                        </div>
                    </div>
                    ${task.imageUrl ? `<img src="${task.imageUrl}" class="task-image" alt="${task.title}">` : ''}
                    <div class="card-body">
                        <p class="card-text">${task.description || 'No description'}</p>
                        ${dueDateHtml}
                        <div class="task-actions">
                            <button class="btn btn-sm btn-outline-primary edit-task">Edit</button>
                            ${task.status === 'pending' 
                                ? `<button class="btn btn-sm btn-success complete-task">Mark Complete</button>` 
                                : `<button class="btn btn-sm btn-warning incomplete-task">Mark Incomplete</button>`}
                            <button class="btn btn-sm btn-danger delete-task">Delete</button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        tasksList.innerHTML = html;
        
        // Add event listeners to task buttons
        addTaskEventListeners();
    }
    
    // Add event listeners to task card buttons
    function addTaskEventListeners() {
        // Edit task buttons
        document.querySelectorAll('.edit-task').forEach(button => {
            button.addEventListener('click', function() {
                const taskCard = this.closest('.task-card');
                const taskId = taskCard.getAttribute('data-id');
                editTask(taskId);
            });
        });
        
        // Complete task buttons
        document.querySelectorAll('.complete-task').forEach(button => {
            button.addEventListener('click', function() {
                const taskCard = this.closest('.task-card');
                const taskId = taskCard.getAttribute('data-id');
                updateTaskStatus(taskId, 'completed');
            });
        });
        
        // Mark as incomplete buttons
        document.querySelectorAll('.incomplete-task').forEach(button => {
            button.addEventListener('click', function() {
                const taskCard = this.closest('.task-card');
                const taskId = taskCard.getAttribute('data-id');
                updateTaskStatus(taskId, 'pending');
            });
        });
        
        // Delete task buttons
        document.querySelectorAll('.delete-task').forEach(button => {
            button.addEventListener('click', function() {
                const taskCard = this.closest('.task-card');
                const taskId = taskCard.getAttribute('data-id');
                confirmDeleteTask(taskId);
            });
        });
    }
    
    // Update task counts
    function updateTaskCounts() {
        if (totalTasksCount) {
            totalTasksCount.textContent = tasks.length;
        }
        
        if (completedTasksCount) {
            const completed = tasks.filter(task => task.status === 'completed').length;
            completedTasksCount.textContent = completed;
        }
        
        if (pendingTasksCount) {
            const pending = tasks.filter(task => task.status === 'pending').length;
            pendingTasksCount.textContent = pending;
        }
    }
    
    // Show task modal for creating a new task
    window.showTaskModal = function() {
        // Reset form
        resetTaskForm();
        
        // Set modal title
        document.getElementById('taskModalLabel').textContent = 'Add New Task';
        
        // Show modal
        taskModal.show();
    };
    
    // Reset task form
    function resetTaskForm() {
        taskForm.reset();
        taskId.value = '';
        taskError.classList.add('d-none');
        currentImageContainer.classList.add('d-none');
        currentTaskImage.src = '';
        originalTaskImageUrl = null;
        shouldRemoveImage = false;
    }
    
    // Edit task - load task data into form
    async function editTask(id) {
        try {
            const response = await fetch(`/tasks/${id}`);
            
            if (!response.ok) {
                throw new Error('Failed to load task');
            }
            
            const task = await response.json();
            
            // Reset form
            resetTaskForm();
            
            // Set form values
            taskId.value = task.id;
            taskTitle.value = task.title;
            taskDescription.value = task.description || '';
            taskStatus.value = task.status;
            taskCategory.value = task.category || '';
            
            // Set urgency if exists, default to medium otherwise
            taskUrgency.value = task.urgency || 'medium';
            
            // Set due date if exists
            if (task.dueDate) {
                taskDueDate.value = task.dueDate;
            } else {
                taskDueDate.value = '';
            }
            
            // Set image if exists
            if (task.imageUrl) {
                currentImageContainer.classList.remove('d-none');
                currentTaskImage.src = task.imageUrl;
                originalTaskImageUrl = task.imageUrl;
            }
            
            // Set modal title
            document.getElementById('taskModalLabel').textContent = 'Edit Task';
            
            // Show modal
            taskModal.show();
        } catch (error) {
            console.error('Error loading task for edit:', error);
            alert('Error loading task: ' + error.message);
        }
    }
    
    // Save task (create or update)
    saveTaskBtn.addEventListener('click', async function() {
        // Reset error
        taskError.classList.add('d-none');
        
        // Validate form
        if (!taskTitle.value.trim()) {
            taskError.textContent = 'Title is required';
            taskError.classList.remove('d-none');
            return;
        }
        
        try {
            const isEdit = taskId.value !== '';
            const url = isEdit ? `/tasks/${taskId.value}` : '/tasks/';
            const method = isEdit ? 'PUT' : 'POST';
            
            // Create form data for file upload
            const formData = new FormData();
            formData.append('title', taskTitle.value.trim());
            formData.append('description', taskDescription.value.trim());
            formData.append('status', taskStatus.value);
            formData.append('category', taskCategory.value);
            
            // Add urgency level
            formData.append('urgency', taskUrgency.value);
            
            // Add due date if specified
            if (taskDueDate.value) {
                formData.append('dueDate', taskDueDate.value);
            }
            
            // Handle image - DEBUG LOGS
            console.log("Image files:", taskImage.files);
            if (taskImage.files.length > 0) {
                console.log("Appending file:", taskImage.files[0]);
                formData.append('image', taskImage.files[0]);
                
                // Debug the FormData
                for (let pair of formData.entries()) {
                    console.log(pair[0] + ': ' + (pair[0] === 'image' ? 'File object' : pair[1]));
                }
            } else if (isEdit && shouldRemoveImage) {
                // If editing and image should be removed
                formData.append('removeImage', 'true');
            }
            
            // Send request with correct headers
            const response = await fetch(url, {
                method: method,
                body: formData,
                // Do not set Content-Type header - browser will set it with boundary
            });
            
            if (!response.ok) {
                // Get error details from response if possible
                let errorMessage = 'Failed to save task';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {}
                
                throw new Error(errorMessage);
            }
            
            // Close modal
            taskModal.hide();
            
            // Reload tasks
            loadTasks();
        } catch (error) {
            console.error('Error saving task:', error);
            taskError.textContent = error.message;
            taskError.classList.remove('d-none');
        }
    });
    
    // Handle remove image button
    removeTaskImage?.addEventListener('click', function() {
        currentImageContainer.classList.add('d-none');
        shouldRemoveImage = true;
    });
    
    // Confirm delete task
    function confirmDeleteTask(id) {
        deleteTaskId.value = id;
        deleteTaskModal.show();
    }
    
    // Delete task
    confirmDeleteTaskBtn.addEventListener('click', async function() {
        const id = deleteTaskId.value;
        
        if (!id) {
            return;
        }
        
        try {
            const response = await fetch(`/tasks/${id}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete task');
            }
            
            // Close modal
            deleteTaskModal.hide();
            
            // Remove task from array
            tasks = tasks.filter(task => task.id !== id);
            
            // Update counts
            updateTaskCounts();
            
            // Re-render with current filter
            applyFilters();
        } catch (error) {
            console.error('Error deleting task:', error);
            alert('Error deleting task: ' + error.message);
        }
    });
    
    // Update task status
    async function updateTaskStatus(id, status) {
        try {
            // Create form data
            const formData = new FormData();
            formData.append('status', status);
            
            const response = await fetch(`/tasks/${id}`, {
                method: 'PUT',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Failed to update task status');
            }
            
            // Update task in array
            const updatedTask = await response.json();
            const index = tasks.findIndex(task => task.id === id);
            
            if (index !== -1) {
                tasks[index] = updatedTask;
            }
            
            // Update counts
            updateTaskCounts();
            
            // Re-render with current filter
            applyFilters();
        } catch (error) {
            console.error('Error updating task status:', error);
            alert('Error updating task: ' + error.message);
        }
    }
}); 