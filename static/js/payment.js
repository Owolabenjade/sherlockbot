// static/js/payment.js - Payment page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializePaymentPage();
});

function initializePaymentPage() {
    // Initialize feedback form if present
    const feedbackForm = document.getElementById('feedbackForm');
    if (feedbackForm) {
        initializeFeedbackForm();
    }
    
    // Initialize copy functionality
    initializeCopyButtons();
    
    // Initialize auto-redirect
    initializeAutoRedirect();
}

function initializeFeedbackForm() {
    const form = document.getElementById('feedbackForm');
    const submitBtn = document.getElementById('submitFeedback');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        submitFeedback();
    });
}

function submitFeedback() {
    const form = document.getElementById('feedbackForm');
    const submitBtn = document.getElementById('submitFeedback');
    const formData = new FormData(form);
    
    // Show loading state
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Submitting...';
    submitBtn.disabled = true;
    
    fetch('/payment/feedback', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showMessage('Thank you for your feedback!', 'success');
            form.style.display = 'none';
        } else {
            showMessage('Error submitting feedback. Please try again.', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Error submitting feedback. Please try again.', 'error');
    })
    .finally(() => {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    });
}

function initializeCopyButtons() {
    const copyButtons = document.querySelectorAll('[data-copy]');
    
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-copy');
            copyToClipboard(textToCopy);
            
            const originalText = this.textContent;
            this.textContent = 'Copied!';
            
            setTimeout(() => {
                this.textContent = originalText;
            }, 2000);
        });
    });
}

function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showMessage('Copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Failed to copy: ', err);
            fallbackCopyTextToClipboard(text);
        });
    } else {
        fallbackCopyTextToClipboard(text);
    }
}

function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    
    // Avoid scrolling to bottom
    textArea.style.top = '0';
    textArea.style.left = '0';
    textArea.style.position = 'fixed';
    
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showMessage('Copied to clipboard!', 'success');
        } else {
            showMessage('Failed to copy to clipboard', 'error');
        }
    } catch (err) {
        console.error('Fallback: Oops, unable to copy', err);
        showMessage('Failed to copy to clipboard', 'error');
    }
    
    document.body.removeChild(textArea);
}

function initializeAutoRedirect() {
    const redirectTimer = document.getElementById('redirectTimer');
    if (redirectTimer) {
        const redirectUrl = redirectTimer.getAttribute('data-url');
        const redirectTime = parseInt(redirectTimer.getAttribute('data-time')) || 10;
        
        let countdown = redirectTime;
        
        const timer = setInterval(() => {
            countdown--;
            redirectTimer.textContent = countdown;
            
            if (countdown <= 0) {
                clearInterval(timer);
                window.location.href = redirectUrl;
            }
        }, 1000);
        
        // Allow user to cancel redirect
        const cancelBtn = document.getElementById('cancelRedirect');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', function() {
                clearInterval(timer);
                redirectTimer.style.display = 'none';
                this.style.display = 'none';
            });
        }
    }
}

function showMessage(message, type) {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.message-alert');
    existingMessages.forEach(msg => msg.remove());
    
    // Create new message
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-alert ${type}-message`;
    messageDiv.textContent = message;
    
    // Insert at top of content
    const content = document.querySelector('.content');
    content.insertBefore(messageDiv, content.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

// Utility function to format currency
function formatCurrency(amount, currency = 'NGN') {
   const formatter = new Intl.NumberFormat('en-NG', {
       style: 'currency',
       currency: currency
   });
   return formatter.format(amount);
}

// Utility function to format dates
function formatDate(dateString) {
   const date = new Date(dateString);
   return date.toLocaleDateString('en-NG', {
       year: 'numeric',
       month: 'long',
       day: 'numeric',
       hour: '2-digit',
       minute: '2-digit'
   });
}

// Payment status checking
function checkPaymentStatus(reference) {
   if (!reference) return;
   
   const statusIndicator = document.getElementById('paymentStatus');
   if (statusIndicator) {
       statusIndicator.textContent = 'Checking payment status...';
   }
   
   fetch(`/payment/status/${reference}`)
       .then(response => response.json())
       .then(data => {
           if (data.status === 'success') {
               showMessage('Payment confirmed!', 'success');
               setTimeout(() => {
                   window.location.reload();
               }, 2000);
           } else if (data.status === 'pending') {
               showMessage('Payment is still processing...', 'info');
               // Check again in 5 seconds
               setTimeout(() => checkPaymentStatus(reference), 5000);
           } else {
               showMessage('Payment verification failed', 'error');
           }
       })
       .catch(error => {
           console.error('Error checking payment status:', error);
           showMessage('Error checking payment status', 'error');
       });
}

// Initialize payment status checking if reference is present
const urlParams = new URLSearchParams(window.location.search);
const paymentReference = urlParams.get('reference');
if (paymentReference && window.location.pathname.includes('success')) {
   // Auto-check payment status on success page
   setTimeout(() => checkPaymentStatus(paymentReference), 1000);
}

// Export functions for use in templates
window.paymentUtils = {
   showMessage,
   formatCurrency,
   formatDate,
   checkPaymentStatus,
   copyToClipboard
};