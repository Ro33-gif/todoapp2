// Wait for the HTML document to fully load before running JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Define variables for user table elements in the HTML
    const usersTableBody = document.getElementById('users-table-body');
    const noUsersMessage = document.getElementById('no-users-message');
    const searchUsers = document.getElementById('searchUsers');
    
    // Define variables for task table elements in the HTML
    const allTasksTableBody = document.getElementById('all-tasks-table-body');
    const noAllTasksMessage = document.getElementById('no-all-tasks-message');
    const searchAllTasks = document.getElementById('searchAllTasks');
    const categoryFilterAdmin = document.getElementById('categoryFilterAdmin');
    
    // Set up variables for the edit user modal window
    const editUserModal = new bootstrap.Modal(document.getElementById('editUserModal'));
    const editUserId = document.getElementById('editUserId');
    const editUserEmail = document.getElementById('editUserEmail');
    const editUserIsAdmin = document.getElementById('editUserIsAdmin');
    const saveUserEdit = document.getElementById('saveUserEdit');
    const editUserError = document.getElementById('edit-user-error');
    
    // Set up variables for the delete user modal window
    const deleteUserModal = new bootstrap.Modal(document.getElementById('deleteUserModal'));
    const deleteUserId = document.getElementById('deleteUserId');
    const deleteUserEmail = document.getElementById('deleteUserEmail');
    const confirmDeleteUser = document.getElementById('confirmDeleteUser');
    const deleteUserError = document.getElementById('delete-user-error');
    
    // Create arrays to store user and task data
    let users = [];
    let allTasks = [];
    
    // Start the initialization function
    init();
    
    // Define the initialization function that runs when the page loads
    async function init() {
        // Check if the current user has admin privileges
        const user = await getCurrentUser();
        if (!user || !await isAdmin(user)) {
            // Redirect to home page if not an admin
            window.location.href = '/';
            return;
        }
        
        // Load user and task data from the server
        loadUsers();
        loadAllTasks();
        
        // Set up event listeners for buttons and inputs
        setupEventListeners();
    }
    
    // Set up all the event listeners for the page elements
    function setupEventListeners() {
        // Add an event listener for the user search input
        searchUsers?.addEventListener('input', filterUsers);
        
        // Add an event listener for the task search input
        searchAllTasks?.addEventListener('input', filterAllTasks);
        
        // Add an event listener for the category filter dropdown
        categoryFilterAdmin?.addEventListener('change', filterAllTasks);
        
        // Add an event listener for the save user edit button
        saveUserEdit?.addEventListener('click', updateUser);
        
        // Add an event listener for the confirm delete user button
        confirmDeleteUser?.addEventListener('click', deleteUser);
    }
    
    // Function to check if a user has admin privileges
    async function isAdmin(user) {
        try {
            // Try to get the user document from Firestore database
            const userDoc = await db.collection('users').doc(user.uid).get();
            if (userDoc.exists) {
                // Convert document to a JavaScript object
                const userData = userDoc.to_dict ? userDoc.to_dict() : userDoc.data();
                // Return true if the user is marked as an admin
                return userData.is_admin === true;
            }
            // Return false if the user document doesn't exist
            return false;
        } catch (error) {
            // Log error and return false if there's a problem
            console.error('Error checking admin status:', error);
            return false;
        }
    }
    
    // Function to fetch all users from the server
    async function loadUsers() {
        try {
            // Show a loading spinner while users are being fetched
            usersTableBody.innerHTML = '<tr><td colspan="5" class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></td></tr>';
            
            // Make a request to the server to get all users
            const response = await fetch('/auth/users');
            
            // Check if the request was successful
            if (!response.ok) {
                throw new Error('Failed to load users');
            }
            
            // Parse the JSON response and store users in the users array
            users = await response.json();
            // Display the users in the table
            renderUsers();
        } catch (error) {
            // Log and display error message if users can't be loaded
            console.error('Error loading users:', error);
            usersTableBody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Error loading users: ${error.message}</td></tr>`;
        }
    }
    
    // Function to display users in the table
    function renderUsers(filteredUsers = null) {
        // Use filtered users if provided, otherwise use all users
        const usersToRender = filteredUsers || users;
        
        // Show "no users" message if there are no users to display
        if (usersToRender.length === 0) {
            usersTableBody.innerHTML = '';
            noUsersMessage.classList.remove('d-none');
            return;
        }
        
        // Hide "no users" message if there are users to display
        noUsersMessage.classList.add('d-none');
        
        // Create HTML string for all users
        let html = '';
        usersToRender.forEach(user => {
            // Format the last active date or show "Never" if not available
            const lastActive = user.lastActive ? new Date(user.lastActive).toLocaleString() : 'Never';
            
            // Add a table row for each user with their data
            html += `
                <tr data-id="${user.id}">
                    <td>${user.email}</td>
                    <td><span class="badge ${user.is_admin ? 'bg-danger' : 'bg-primary'}">${user.is_admin ? 'Admin' : 'User'}</span></td>
                    <td>${user.taskCount || 0}</td>
                    <td>${lastActive}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary edit-user">Edit</button>
                        <button class="btn btn-sm btn-danger delete-user">Delete</button>
                    </td>
                </tr>
            `;
        });
        
        // Set the HTML content of the users table
        usersTableBody.innerHTML = html;
        
        // Add event listeners to the buttons in the table
        addUserActionListeners();
    }
    
    // Function to add event listeners to the edit and delete buttons
    function addUserActionListeners() {
        // Add click event listeners to all edit user buttons
        document.querySelectorAll('.edit-user').forEach(button => {
            button.addEventListener('click', function() {
                // Get the user ID from the table row
                const userId = this.closest('tr').getAttribute('data-id');
                // Open the edit user modal for this user
                showEditUserModal(userId);
            });
        });
        
        // Add click event listeners to all delete user buttons
        document.querySelectorAll('.delete-user').forEach(button => {
            button.addEventListener('click', function() {
                // Get the user ID from the table row
                const userId = this.closest('tr').getAttribute('data-id');
                // Open the delete user modal for this user
                showDeleteUserModal(userId);
            });
        });
    }
    
    // Function to filter users based on search input
    function filterUsers() {
        // Get the search term from the input field
        const searchTerm = searchUsers.value.toLowerCase().trim();
        
        // If search term is empty, show all users
        if (!searchTerm) {
            renderUsers();
            return;
        }
        
        // Filter users whose email contains the search term
        const filtered = users.filter(user => 
            user.email.toLowerCase().includes(searchTerm)
        );
        
        // Display the filtered users
        renderUsers(filtered);
    }
    
    // Function to fetch all tasks from the server
    async function loadAllTasks() {
        try {
            // Show a loading spinner while tasks are being fetched
            allTasksTableBody.innerHTML = '<tr><td colspan="6" class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></td></tr>';
            
            // Make a request to the server to get all tasks
            const response = await fetch('/tasks/admin/all');
            
            // Check if the request was successful
            if (!response.ok) {
                throw new Error('Failed to load tasks');
            }
            
            // Parse the JSON response and store tasks in the allTasks array
            allTasks = await response.json();
            // Filter and display the tasks
            filterAllTasks();
        } catch (error) {
            // Log and display error message if tasks can't be loaded
            console.error('Error loading all tasks:', error);
            allTasksTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error loading tasks: ${error.message}</td></tr>`;
        }
    }
    
    // Function to filter and display tasks based on search and category
    function filterAllTasks() {
        // Get the search term and category filter values
        const searchTerm = searchAllTasks?.value.toLowerCase().trim() || '';
        const categoryFilter = categoryFilterAdmin?.value || 'all';
        
        // Create a copy of all tasks to filter
        let filteredTasks = [...allTasks];
        
        // Apply category filter
        if (categoryFilter !== 'all') {
            filteredTasks = filteredTasks.filter(task => task.category === categoryFilter);
        }
        
        // Apply search filter
        if (searchTerm) {
            filteredTasks = filteredTasks.filter(task => 
                task.title.toLowerCase().includes(searchTerm) ||
                (task.description && task.description.toLowerCase().includes(searchTerm)) ||
                task.userEmail.toLowerCase().includes(searchTerm)
            );
        }
        
        renderAllTasks(filteredTasks);
    }
    
    // Render all tasks table
    function renderAllTasks(filteredTasks) {
        if (filteredTasks.length === 0) {
            allTasksTableBody.innerHTML = '';
            noAllTasksMessage.classList.remove('d-none');
            return;
        }
        
        noAllTasksMessage.classList.add('d-none');
        
        let html = '';
        filteredTasks.forEach(task => {
            const createdAt = new Date(task.createdAt).toLocaleString();
            const statusBadge = task.status === 'completed' 
                ? '<span class="badge bg-success">Completed</span>' 
                : '<span class="badge bg-warning text-dark">Pending</span>';
            
            html += `
                <tr data-id="${task.id}">
                    <td>${task.title}</td>
                    <td>${task.userEmail}</td>
                    <td><span class="badge bg-info">${task.category || 'None'}</span></td>
                    <td>${statusBadge}</td>
                    <td>${createdAt}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary view-task">View</button>
                        <button class="btn btn-sm btn-danger delete-task">Delete</button>
                    </td>
                </tr>
            `;
        });
        
        allTasksTableBody.innerHTML = html;
        
        // Add event listeners to task action buttons
        addTaskActionListeners();
    }
    
    // Add event listeners to task action buttons
    function addTaskActionListeners() {
        // View task buttons
        document.querySelectorAll('.view-task').forEach(button => {
            button.addEventListener('click', function() {
                const taskId = this.closest('tr').getAttribute('data-id');
                viewTask(taskId);
            });
        });
        
        // Delete task buttons
        document.querySelectorAll('.delete-task').forEach(button => {
            button.addEventListener('click', function() {
                const taskId = this.closest('tr').getAttribute('data-id');
                deleteTask(taskId);
            });
        });
    }
    
    // Show edit user modal
    function showEditUserModal(userId) {
        const user = users.find(u => u.id === userId);
        
        if (!user) {
            return;
        }
        
        // Set modal values
        editUserId.value = user.id;
        editUserEmail.value = user.email;
        editUserIsAdmin.checked = user.is_admin === true;
        
        // Reset error
        editUserError.classList.add('d-none');
        
        // Show modal
        editUserModal.show();
    }
    
    // Update user admin status
    async function updateUser() {
        const userId = editUserId.value;
        const is_admin = editUserIsAdmin.checked;
        
        if (!userId) {
            return;
        }
        
        try {
            const response = await fetch(`/auth/users/${userId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ is_admin })
            });
            
            if (!response.ok) {
                throw new Error('Failed to update user');
            }
            
            // Update user in array
            const updatedUser = await response.json();
            const index = users.findIndex(u => u.id === userId);
            
            if (index !== -1) {
                users[index] = updatedUser;
            }
            
            // Close modal
            editUserModal.hide();
            
            // Re-render users
            renderUsers();
        } catch (error) {
            console.error('Error updating user:', error);
            editUserError.textContent = error.message;
            editUserError.classList.remove('d-none');
        }
    }
    
    // Show delete user modal
    function showDeleteUserModal(userId) {
        const user = users.find(u => u.id === userId);
        
        if (!user) {
            return;
        }
        
        // Set modal values
        deleteUserId.value = user.id;
        deleteUserEmail.textContent = user.email;
        
        // Reset error
        deleteUserError.classList.add('d-none');
        
        // Show modal
        deleteUserModal.show();
    }
    
    // Delete user
    async function deleteUser() {
        const userId = deleteUserId.value;
        
        if (!userId) {
            return;
        }
        
        try {
            const response = await fetch(`/auth/users/${userId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete user');
            }
            
            // Remove user from array
            users = users.filter(u => u.id !== userId);
            
            // Close modal
            deleteUserModal.hide();
            
            // Re-render users
            renderUsers();
        } catch (error) {
            console.error('Error deleting user:', error);
            deleteUserError.textContent = error.message;
            deleteUserError.classList.remove('d-none');
        }
    }
    
    // View task details
    function viewTask(taskId) {
        // Navigate to task page or show task details modal
        // Implementation depends on your app's design
        console.log(`View task: ${taskId}`);
    }
    
    // Delete task
    async function deleteTask(taskId) {
        if (!confirm('Are you sure you want to delete this task?')) {
            return;
        }
        
        try {
            const response = await fetch(`/tasks/${taskId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete task');
            }
            
            // Remove task from array
            allTasks = allTasks.filter(t => t.id !== taskId);
            
            // Re-render tasks
            filterAllTasks();
        } catch (error) {
            console.error('Error deleting task:', error);
            alert(`Error deleting task: ${error.message}`);
        }
    }
}); 