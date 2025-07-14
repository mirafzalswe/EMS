// Navigation functionality
document.querySelectorAll('.nav-item > .nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        if (link.nextElementSibling && link.nextElementSibling.classList.contains('subnav')) {
            e.preventDefault();
            const navItem = link.parentElement;
            navItem.classList.toggle('expanded');
        }
    });
});

// Theme toggle
const themeToggle = document.getElementById('themeToggle');
const body = document.body;

// Load saved theme
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    body.classList.add('dark-theme');
    themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
}

themeToggle.addEventListener('click', () => {
    body.classList.toggle('dark-theme');
    if (body.classList.contains('dark-theme')) {
        themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        localStorage.setItem('theme', 'dark');
    } else {
        themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        localStorage.setItem('theme', 'light');
    }
});

// Mobile menu functionality
const mobileMenuToggle = document.getElementById('mobileMenuToggle');
const verticalNavbar = document.getElementById('verticalNavbar');
const mobileOverlay = document.getElementById('mobileOverlay');

function toggleMobileMenu() {
    verticalNavbar.classList.toggle('mobile-visible');
    mobileOverlay.classList.toggle('active');
}

function closeMobileMenu() {
    verticalNavbar.classList.remove('mobile-visible');
    mobileOverlay.classList.remove('active');
}

mobileMenuToggle.addEventListener('click', toggleMobileMenu);
mobileOverlay.addEventListener('click', closeMobileMenu);

// Close mobile menu on escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeMobileMenu();
    }
});

// Handle window resize
window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
        closeMobileMenu();
    }
});

// Active page highlighting
function setActiveNavItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// Set active nav item on page load
document.addEventListener('DOMContentLoaded', setActiveNavItem);

// Search functionality
const searchInput = document.querySelector('.search-input');
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        // Implement search functionality here
        console.log('Search:', e.target.value);
    }
});