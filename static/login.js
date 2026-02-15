// Floating label effect
document.querySelectorAll('.inputBox input').forEach(input => {
    input.addEventListener('focus', () => {
        input.parentElement.classList.add('active');
    });

    input.addEventListener('blur', () => {
        if (input.value === '') {
            input.parentElement.classList.remove('active');
        }
    });
});

// Form submission animation
const form = document.querySelector('.form');

form.addEventListener('submit', function (e) {
    const username = form.querySelector('input[name="username"]').value.trim();
    const password = form.querySelector('input[name="password"]').value.trim();

    // Basic validation
    if (!username || !password) {
        e.preventDefault();
        alert("Please enter both username and password.");
        return;
    }

    // Button loading effect
    const button = form.querySelector('input[type="submit"]');
    button.value = "Signing in...";
    button.disabled = true;
});
