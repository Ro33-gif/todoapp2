// Wait for the HTML document to fully load before running JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Get references to login and registration buttons
    const btnLogin = document.getElementById('btnLogin');
    const btnRegister = document.getElementById('btnRegister');
    const btnLogout = document.getElementById('btnLogout');
    // Create modal objects for login and registration popups
    const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
    const registerModal = new bootstrap.Modal(document.getElementById('registerModal'));
    
    // Get references to login form elements
    const loginForm = document.getElementById('loginForm');
    const loginEmail = document.getElementById('loginEmail');
    const loginPassword = document.getElementById('loginPassword');
    const loginSubmit = document.getElementById('loginSubmit');
    const loginError = document.getElementById('loginError');
    
    // Get references to registration form elements
    const registerForm = document.getElementById('registerForm');
    const registerEmail = document.getElementById('registerEmail');
    const registerPassword = document.getElementById('registerPassword');
    const registerPasswordConfirm = document.getElementById('registerPasswordConfirm');
    const registerSubmit = document.getElementById('registerSubmit');
    const registerError = document.getElementById('registerError');
    
    // Add click event listener to show login modal when login button is clicked
    btnLogin?.addEventListener('click', function() {
        loginModal.show();
    });
    
    // Add click event listener to show registration modal when register button is clicked
    btnRegister?.addEventListener('click', function() {
        registerModal.show();
    });
    
    // Add click event listener to switch from login to register modal
    document.getElementById('showRegister')?.addEventListener('click', function(e) {
        // Prevent default link behavior
        e.preventDefault();
        // Hide the login modal
        loginModal.hide();
        // Wait 500ms before showing register modal for smooth transition
        setTimeout(() => {
            registerModal.show();
        }, 500);
    });
    
    // Add click event listener to switch from register to login modal
    document.getElementById('showLogin')?.addEventListener('click', function(e) {
        // Prevent default link behavior
        e.preventDefault();
        // Hide the register modal
        registerModal.hide();
        // Wait 500ms before showing login modal for smooth transition
        setTimeout(() => {
            loginModal.show();
        }, 500);
    });
    
    // Add click event listener for login form submission
    loginSubmit?.addEventListener('click', async function() {
        // Hide previous error messages
        loginError.classList.add('d-none');
        
        // Get email and password values from form
        const email = loginEmail.value.trim();
        const password = loginPassword.value;
        
        // Validate that email and password are provided
        if (!email || !password) {
            // Display error if fields are empty
            loginError.textContent = 'Please enter both email and password';
            loginError.classList.remove('d-none');
            return;
        }
        
        try {
            // Attempt to sign in using Firebase Authentication
            const userCredential = await auth.signInWithEmailAndPassword(email, password);
            // Get the user object from credentials
            const user = userCredential.user;
            
            // Check if user exists
            if (!user) {
                throw new Error('User authentication failed');
            }
            
            // Get the authentication token for the user
            const idToken = await user.getIdToken();
            
            // Verify token exists
            if (!idToken) {
                throw new Error('Failed to get authentication token');
            }
            
            // Send token to server to create session
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ idToken }),
            });
            
            // Parse server response
            const responseData = await response.json();
            
            // Check if server response is successful
            if (!response.ok) {
                throw new Error(responseData.error || 'Failed to authenticate with server');
            }
            
            // Log success message
            console.log('Login successful:', responseData);
            
            // Close the login modal and reset form
            loginModal.hide();
            loginForm.reset();
            // Redirect to homepage
            window.location.href = '/';
        } catch (error) {
            // Log error to console
            console.error('Login error:', error);
            // Display error message to user
            loginError.textContent = error.message;
            loginError.classList.remove('d-none');
        }
    });
    
    // Add click event listener for registration form submission
    registerSubmit?.addEventListener('click', async function() {
        // Hide previous error messages
        registerError.classList.add('d-none');
        
        // Get form values
        const email = registerEmail.value.trim();
        const password = registerPassword.value;
        const passwordConfirm = registerPasswordConfirm.value;
        
        // Validate that email and password are provided
        if (!email || !password) {
            // Display error if fields are empty
            registerError.textContent = 'Please enter both email and password';
            registerError.classList.remove('d-none');
            return;
        }
        
        // Validate password length
        if (password.length < 6) {
            // Display error if password is too short
            registerError.textContent = 'Password must be at least 6 characters';
            registerError.classList.remove('d-none');
            return;
        }
        
        // Validate that passwords match
        if (password !== passwordConfirm) {
            // Display error if passwords don't match
            registerError.textContent = 'Passwords do not match';
            registerError.classList.remove('d-none');
            return;
        }
        
        try {
            // Create new user in Firebase Authentication
            const userCredential = await auth.createUserWithEmailAndPassword(email, password);
            
            // Send registration data to backend server
            const response = await fetch('/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    email,
                    password
                }),
            });
            
            // Check if server response is successful
            if (!response.ok) {
                throw new Error('Failed to register with server');
            }
            
            // Close registration modal and reset form
            registerModal.hide();
            registerForm.reset();
            // Redirect to homepage
            window.location.href = '/';
        } catch (error) {
            // Log error to console
            console.error('Registration error:', error);
            // Display error message to user
            registerError.textContent = error.message;
            registerError.classList.remove('d-none');
        }
    });
    
    // Add click event listener for logout button
    btnLogout?.addEventListener('click', async function() {
        try {
            // Sign out from Firebase Authentication
            await auth.signOut();
            
            // Call server logout endpoint to clear session
            await fetch('/auth/logout', {
                method: 'POST',
            });
            
            // Redirect to homepage
            window.location.href = '/';
        } catch (error) {
            // Log error to console
            console.error('Logout error:', error);
        }
    });
    
    // Add click event listener for Google login button
    document.getElementById('googleLogin')?.addEventListener('click', function() {
        // Create Google authentication provider
        const provider = new firebase.auth.GoogleAuthProvider();
        // Call function to handle Google sign-in
        signInWithGoogle(provider);
    });
    
    // Add click event listener for Google registration button
    document.getElementById('googleRegister')?.addEventListener('click', function() {
        // Create Google authentication provider
        const provider = new firebase.auth.GoogleAuthProvider();
        // Call function to handle Google sign-in
        signInWithGoogle(provider);
    });
    
    // Function to handle Google authentication
    async function signInWithGoogle(provider) {
        try {
            // Open Google sign-in popup and get result
            const result = await auth.signInWithPopup(provider);
            // Get user from result
            const user = result.user;
            
            // Get authentication token for server
            const idToken = await user.getIdToken();
            
            // Send token to server to create session
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ idToken }),
            });
            
            // Parse server response
            const responseData = await response.json();
            
            // Check if server response is successful
            if (!response.ok) {
                throw new Error(responseData.error || 'Failed to authenticate with server');
            }
            
            // Log success message
            console.log('Google login successful:', responseData);
            
            // Redirect to homepage
            window.location.href = '/';
        } catch (error) {
            // Log error to console
            console.error('Google sign-in error:', error);
            // Display error message in appropriate modal
            const activeModal = document.querySelector('.modal.show');
            if (activeModal) {
                const errorElement = activeModal.querySelector('.auth-error');
                if (errorElement) {
                    errorElement.textContent = error.message;
                    errorElement.classList.remove('d-none');
                }
            }
        }
    }
    
    // Check authentication state on page load
    checkAuthState();
    
    // Function to check if user is already logged in
    async function checkAuthState() {
        // Add auth state change listener to Firebase
        auth.onAuthStateChanged(async (user) => {
            // Update UI based on user login state
            updateUI(user);
        });
    }
    
    // Function to update UI based on user login state
    function updateUI(user) {
        const userMenu = document.getElementById('userMenu');
        const guestMenu = document.getElementById('guestMenu');
        const userEmail = document.getElementById('userEmail');
        
        if (user) {
            // If user is logged in, show user menu and hide guest menu
            userMenu?.classList.remove('d-none');
            guestMenu?.classList.add('d-none');
            // Update displayed email
            if (userEmail) {
                userEmail.textContent = user.email;
            }
        } else {
            // If user is not logged in, hide user menu and show guest menu
            userMenu?.classList.add('d-none');
            guestMenu?.classList.remove('d-none');
        }
    }
}); 