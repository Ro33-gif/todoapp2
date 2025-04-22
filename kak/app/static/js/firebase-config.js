// Define Firebase configuration with API keys and project settings
const firebaseConfig = {
    // Your Firebase API key for authentication
    apiKey: "AIzaSyATj9K1Ewf_Bo62BROdlb2hFBXTSgP-BWY",
    // Your Firebase auth domain for authentication services
    authDomain: "roeeki-a4ca2.firebaseapp.com",
    // Your Firebase project ID
    projectId: "roeeki-a4ca2",
    // Your Firebase storage bucket for file storage
    storageBucket: "roeeki-a4ca2.appspot.com",
    // Your Firebase messaging sender ID for notifications
    messagingSenderId: "137045971039",
    // Your Firebase application ID
    appId: "1:137045971039:web:YOUR_APP_ID"
};

// Initialize Firebase with the configuration settings
firebase.initializeApp(firebaseConfig);

// Get references to Firebase services that will be used in the app
// Get the authentication service
const auth = firebase.auth();
// Get the Firestore database service
const db = firebase.firestore();
// Get the Firebase storage service
const storage = firebase.storage();

// Set authentication persistence to keep users logged in across browser sessions
auth.setPersistence(firebase.auth.Auth.Persistence.LOCAL);

// Define a function to get the currently authenticated user
function getCurrentUser() {
    // Return a promise that resolves with the current user
    return new Promise((resolve, reject) => {
        // Listen for authentication state changes
        const unsubscribe = auth.onAuthStateChanged(user => {
            // Stop listening once we get the result
            unsubscribe();
            // Return the user object (or null if not logged in)
            resolve(user);
        }, reject);
    });
}

// Define a function to get the authentication token for the current user
async function getIdToken() {
    // Get the current user
    const user = await getCurrentUser();
    // If a user is logged in
    if (user) {
        // Return their authentication token
        return user.getIdToken();
    }
    // Return null if no user is logged in
    return null;
}

// Add a listener to update the UI whenever authentication state changes
auth.onAuthStateChanged(user => {
    // Get all elements that should only be visible to guests (non-logged in users)
    const guestElements = document.querySelectorAll('.guest-only');
    // Get all elements that should only be visible to logged in users
    const userElements = document.querySelectorAll('.user-only');
    // Get all elements that should only be visible to admin users
    const adminElements = document.querySelectorAll('.admin-only');
    
    // Check if the current page is the admin page
    const isAdminPage = window.location.pathname === '/admin';

    if (user) {
        // If a user is logged in
        // Hide all guest-only elements
        guestElements.forEach(el => el.classList.add('d-none'));
        // Show all user-only elements
        userElements.forEach(el => el.classList.remove('d-none'));
        
        // Check if the logged in user is an admin
        db.collection('users').doc(user.uid).get().then(doc => {
            // If the user document exists and has admin flag set to true
            if (doc.exists && doc.data().is_admin === true) {
                // Show all admin-only elements
                adminElements.forEach(el => el.classList.remove('d-none'));
            } else {
                // Hide all admin-only elements
                adminElements.forEach(el => el.classList.add('d-none'));
                
                // If the user is on the admin page but isn't an admin, redirect to homepage
                if (isAdminPage) {
                    window.location.href = '/';
                }
            }
        });
    } else {
        // If no user is logged in
        // Show all guest-only elements
        guestElements.forEach(el => el.classList.remove('d-none'));
        // Hide all user-only elements
        userElements.forEach(el => el.classList.add('d-none'));
        // Hide all admin-only elements
        adminElements.forEach(el => el.classList.add('d-none'));
        
        // If the user is on the admin page but not logged in, redirect to homepage
        if (isAdminPage) {
            window.location.href = '/';
        }
    }
}); 