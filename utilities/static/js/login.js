document.getElementById('login-form').addEventListener('submit', function(e) {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('login-error');
    const urlParams = new URLSearchParams(window.location.search);
    let url = '/login';

    if (urlParams.has('admin')) {
        url += "?admin";
    }

    fetch (url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(
            {
            email: email, 
            password: password
        }
            ),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '/';  // Redirect on success to chatbot screen
        } else {
            errorMessage.textContent = 'Login failed. Please try again.';
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        errorMessage.textContent = 'An error occurred. Please try again.';
    });
});

