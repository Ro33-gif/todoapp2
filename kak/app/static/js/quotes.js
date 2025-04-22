document.addEventListener('DOMContentLoaded', function() {
    // DOM elements for quotes
    const quoteContent = document.getElementById('quote-content');
    const quoteAuthor = document.getElementById('quote-author');
    const quoteCategory = document.getElementById('quote-category');
    const refreshQuoteBtn = document.getElementById('refresh-quote');
    
    // Function to fetch a new quote from the API
    async function fetchQuote() {
        try {
            // Show loading state
            if (quoteContent && quoteAuthor) {
                quoteContent.innerHTML = '<div class="d-flex justify-content-center"><div class="spinner-border text-primary spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div></div>';
                quoteAuthor.textContent = '';
                if (quoteCategory) quoteCategory.textContent = '';
            }
            
            // Add a timestamp to prevent caching
            const timestamp = new Date().getTime();
            const response = await fetch(`/quote?_=${timestamp}`);
            
            if (!response.ok) {
                throw new Error('Failed to fetch quote');
            }
            
            const data = await response.json();
            
            // Update the UI with the quote
            if (quoteContent && quoteAuthor) {
                quoteContent.textContent = `"${data.content}"`;
                quoteAuthor.textContent = `- ${data.author}`;
                
                // Display category if available
                if (quoteCategory && data.category) {
                    quoteCategory.textContent = data.category;
                    quoteCategory.classList.remove('d-none');
                } else if (quoteCategory) {
                    quoteCategory.classList.add('d-none');
                }
            }
            
            // Store the quote in localStorage
            localStorage.setItem('savedQuote', JSON.stringify({
                content: data.content,
                author: data.author,
                category: data.category
            }));
        } catch (error) {
            console.error('Error fetching quote:', error);
            
            // Show fallback quote if fetch fails
            if (quoteContent && quoteAuthor) {
                quoteContent.textContent = '"The will of man is his happiness."';
                quoteAuthor.textContent = '- Friedrich Schiller';
                if (quoteCategory) {
                    quoteCategory.textContent = 'happiness';
                    quoteCategory.classList.remove('d-none');
                }
            }
        }
    }
    
    // Load the saved quote or fetch a new one if none exists
    function loadQuote() {
        const storedQuote = localStorage.getItem('savedQuote');
        
        if (storedQuote) {
            // Use the stored quote
            const quoteData = JSON.parse(storedQuote);
            if (quoteContent && quoteAuthor) {
                quoteContent.textContent = `"${quoteData.content}"`;
                quoteAuthor.textContent = `- ${quoteData.author}`;
                
                // Display category if available
                if (quoteCategory && quoteData.category) {
                    quoteCategory.textContent = quoteData.category;
                    quoteCategory.classList.remove('d-none');
                } else if (quoteCategory) {
                    quoteCategory.classList.add('d-none');
                }
            }
        } else {
            // No stored quote, fetch a new one
            fetchQuote();
        }
    }
    
    // Load quote when page loads
    if (quoteContent && quoteAuthor) {
        loadQuote();
    }
    
    // Add event listener for refresh button
    refreshQuoteBtn?.addEventListener('click', function() {
        fetchQuote();
    });
}); 