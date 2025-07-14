// Teacher Slider functionality with improved animations
class TeacherSlider {
    constructor() {
        this.slider = document.querySelector('.edu-teachers__slider');
        this.track = document.querySelector('.edu-teachers__track');
        this.slides = Array.from(document.querySelectorAll('.edu-teacher__slide'));
        this.dots = Array.from(document.querySelectorAll('.edu-slider__dot'));
        this.prevBtn = document.querySelector('.edu-slider__btn--prev');
        this.nextBtn = document.querySelector('.edu-slider__btn--next');
        this.currentSlide = 0;
        this.slidesCount = this.slides.length;
        this.autoplayInterval = null;
        this.isAnimating = false;
        this.touchStartX = 0;
        this.touchEndX = 0;
        this.animationDuration = 800; // Match with CSS transition duration (in ms)
        
        this.init();
    }

    init() {
        // Set initial active slide
        if (this.slides.length > 0) {
            this.slides[0].classList.add('active');
            this.dots[0].classList.add('active');
        }
        
        // Add event listeners
        this.prevBtn.addEventListener('click', () => this.prevSlide());
        this.nextBtn.addEventListener('click', () => this.nextSlide());
        
        // Add dot click handlers
        this.dots.forEach((dot, index) => {
            dot.addEventListener('click', () => this.goToSlide(index));
        });

        // Add keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') this.prevSlide();
            if (e.key === 'ArrowRight') this.nextSlide();
        });
        
        // Add touch events for swipe on mobile
        this.track.addEventListener('touchstart', (e) => {
            this.touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });
        
        this.track.addEventListener('touchend', (e) => {
            this.touchEndX = e.changedTouches[0].screenX;
            this.handleSwipe();
        }, { passive: true });
        
        // Add intersection observer for section animation
        this.initSectionAnimations();
        
        // Start autoplay
        this.startAutoplay();
        
        // Pause autoplay on hover
        this.slider.addEventListener('mouseenter', () => this.pauseAutoplay());
        this.slider.addEventListener('mouseleave', () => this.startAutoplay());
        
        // Pause autoplay on touch
        this.slider.addEventListener('touchstart', () => this.pauseAutoplay(), { passive: true });
        this.slider.addEventListener('touchend', () => this.startAutoplay(), { passive: true });
    }
    
    initSectionAnimations() {
        // For elements with data-aos attribute
        const animatedElements = document.querySelectorAll('[data-aos]');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const animationType = entry.target.getAttribute('data-aos');
                    entry.target.classList.add(animationType);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.2 });

        animatedElements.forEach(el => observer.observe(el));
    }
    
    handleSwipe() {
        const swipeThreshold = 50;
        const swipeDistance = this.touchEndX - this.touchStartX;
        
        if (swipeDistance > swipeThreshold) {
            this.prevSlide(); // Swipe right
        } else if (swipeDistance < -swipeThreshold) {
            this.nextSlide(); // Swipe left
        }
    }

    goToSlide(index) {
        if (this.isAnimating || index === this.currentSlide) return;
        this.isAnimating = true;
        
        // Remove active class from current slide and dot
        this.slides[this.currentSlide].classList.remove('active');
        this.dots[this.currentSlide].classList.remove('active');
        
        // Update current slide
        this.currentSlide = index;
        
        // Add active class to new slide and dot
        this.slides[this.currentSlide].classList.add('active');
        this.dots[this.currentSlide].classList.add('active');
        
        // Reset animation state after transition completes
        setTimeout(() => {
            this.isAnimating = false;
        }, this.animationDuration);
    }

    nextSlide() {
        const nextIndex = (this.currentSlide + 1) % this.slidesCount;
        this.goToSlide(nextIndex);
    }

    prevSlide() {
        const prevIndex = (this.currentSlide - 1 + this.slidesCount) % this.slidesCount;
        this.goToSlide(prevIndex);
    }
    
    startAutoplay() {
        // Clear any existing interval
        this.pauseAutoplay();
        
        // Start new autoplay interval
        this.autoplayInterval = setInterval(() => {
            this.nextSlide();
        }, 5000);
    }
    
    pauseAutoplay() {
        if (this.autoplayInterval) {
            clearInterval(this.autoplayInterval);
            this.autoplayInterval = null;
        }
    }
}

// Animation function for the teachers section
function initTeachersAnimations() {
    // Make sure GSAP and ScrollTrigger are registered
    gsap.registerPlugin(ScrollTrigger);
    
    // Animate the title
    gsap.from('.edu-section__title', {
        y: -50,
        opacity: 0,
        duration: 1.2,
        scrollTrigger: {
            trigger: '.edu-teachers',
            start: 'top bottom-=100',
            toggleActions: 'play none none none'
        },
        onComplete: function() {
            // Add the active class for the underline animation
            document.querySelector('.edu-section__title').classList.add('active');
            
            // Create floating letters effect
            const title = document.querySelector('.edu-section__title');
            const text = title.textContent;
            let newText = '';
            
            for (let i = 0; i < text.length; i++) {
                newText += `<span class="letter">${text[i]}</span>`;
            }
            
            title.innerHTML = newText;
        }
    });
    
    // Animate the subtitle
    gsap.from('.edu-teachers__subtitle', {
        y: 30,
        opacity: 0,
        duration: 1,
        delay: 0.3,
        scrollTrigger: {
            trigger: '.edu-teachers',
            start: 'top bottom-=100',
            toggleActions: 'play none none none'
        }
    });
    
    // Create a staggered reveal effect for teacher cards (assuming you'll add them)
    gsap.utils.toArray('.teacher-card').forEach((card, i) => {
        gsap.from(card, {
            y: 100,
            opacity: 0,
            duration: 1,
            delay: i * 0.2,
            scrollTrigger: {
                trigger: card,
                start: 'top bottom-=100',
                toggleActions: 'play none none none'
            }
        });
    });
    
    // Add hover effect for teacher cards
    const teacherCards = document.querySelectorAll('.teacher-card');
    teacherCards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            gsap.to(card, {
                y: -10,
                scale: 1.05,
                boxShadow: '0 15px 30px rgba(0, 0, 0, 0.3)',
                duration: 0.3
            });
        });
        
        card.addEventListener('mouseleave', () => {
            gsap.to(card, {
                y: 0,
                scale: 1,
                boxShadow: '0 8px 20px rgba(0, 0, 0, 0.2)',
                duration: 0.3
            });
        });
    });
    
    // Create a parallax effect for the background
    gsap.to('.edu-teachers', {
        backgroundPosition: '50% 100%',
        ease: 'none',
        scrollTrigger: {
            trigger: '.edu-teachers',
            start: 'top bottom',
            end: 'bottom top',
            scrub: true
        }
    });
}

// Initialize animations when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initTeachersAnimations();
});

// Initialize slider when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Add global animation enhancement
    const enhanceAnimations = () => {
        // Add staggered animation for tags
        const allTags = document.querySelectorAll('.edu-teacher__tag');
        allTags.forEach((tag, index) => {
            tag.style.transitionDelay = `${index * 0.1}s`;
        });
        
        // Add hover effect for cards
        const mainCards = document.querySelectorAll('.edu-teacher__card--main');
        mainCards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'scale(1.12) translateY(-5px)';
            });
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'scale(1.1)';
            });
        });
    };
    
    // Smooth scroll for anchor links
    const smoothScroll = () => {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                
                const targetId = this.getAttribute('href');
                if (targetId === '#') return;
                
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    };
    
    // Initialize the slider
    const teacherSlider = new TeacherSlider();
    
    // Apply other enhancements
    enhanceAnimations();
    smoothScroll();
});

// Theme Toggle
const themeToggle = document.querySelector('.edu-navbar__theme-toggle');
const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');

// Check for saved theme preference or default to user's system preference
const getCurrentTheme = () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        return savedTheme;
    }
    return prefersDarkScheme.matches ? 'dark' : 'light';
};

// Set theme
const setTheme = (theme) => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
};

// Initialize theme
setTheme(getCurrentTheme());

// Theme toggle click handler
themeToggle.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
});

// Mobile Menu
const mobileToggle = document.querySelector('.edu-navbar__mobile-toggle');
const mobileMenu = document.querySelector('.edu-navbar__mobile-menu');
const body = document.body;

mobileToggle.addEventListener('click', () => {
    mobileToggle.classList.toggle('active');
    mobileMenu.classList.toggle('active');
    body.classList.toggle('no-scroll');
});

// Close mobile menu when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.edu-navbar__mobile-menu') && 
        !e.target.closest('.edu-navbar__mobile-toggle') && 
        mobileMenu.classList.contains('active')) {
        mobileMenu.classList.remove('active');
        mobileToggle.classList.remove('active');
        body.classList.remove('no-scroll');
    }
});

// Navbar Scroll Effect
const navbar = document.querySelector('.edu-navbar');
let lastScroll = 0;

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    
    if (currentScroll <= 0) {
        navbar.classList.remove('scrolled');
        navbar.classList.remove('scroll-up');
        return;
    }
    
    if (currentScroll > lastScroll && !navbar.classList.contains('scroll-down')) {
        // Scrolling down
        navbar.classList.remove('scroll-up');
        navbar.classList.add('scroll-down');
    } else if (currentScroll < lastScroll && navbar.classList.contains('scroll-down')) {
        // Scrolling up
        navbar.classList.remove('scroll-down');
        navbar.classList.add('scroll-up');
    }

    if (currentScroll > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
    
    lastScroll = currentScroll;
});

// Smooth Scroll for Navigation Links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            // Close mobile menu if open
            mobileMenu.classList.remove('active');
            mobileToggle.classList.remove('active');
            body.classList.remove('no-scroll');
            
            // Smooth scroll to target
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const heroSection = document.querySelector('.edu-hero');
    const particlesContainer = document.createElement('div');
    particlesContainer.classList.add('edu-hero__particles');
    
    // Create particles
    for (let i = 0; i < 15; i++) {
        const particle = document.createElement('div');
        particle.classList.add('edu-particle');
        
        // Random properties
        const size = Math.random() * 6 + 3;
        const opacity = Math.random() * 0.5 + 0.1;
        const x1 = Math.random() * 400 - 200;
        const y1 = Math.random() * 400 - 200;
        const x2 = Math.random() * 400 - 200;
        const y2 = Math.random() * 400 - 200;
        
        // Apply styles
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.opacity = opacity;
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;
        particle.style.setProperty('--x1', `${x1}px`);
        particle.style.setProperty('--y1', `${y1}px`);
        particle.style.setProperty('--x2', `${x2}px`);
        particle.style.setProperty('--y2', `${y2}px`);
        
        particlesContainer.appendChild(particle);
    }
    
    heroSection.appendChild(particlesContainer);
    
    // Add mouse parallax effect
    heroSection.addEventListener('mousemove', function(e) {
        const moveX = (e.clientX - window.innerWidth / 2) / 50;
        const moveY = (e.clientY - window.innerHeight / 2) / 50;
        
        document.querySelector('.edu-hero__content').style.transform = 
            `translateZ(0) translate(${-moveX / 2}px, ${-moveY / 2}px)`;
            
        document.querySelector('.edu-hero__stats').style.transform = 
            `translateZ(0) translate(${moveX}px, ${moveY}px)`;
    });
});

// Feature Section

// Initialize 3D background
function initCosmicBackground() {
    const canvas = document.getElementById('cosmicBackground');
    const renderer = new THREE.WebGLRenderer({
        canvas,
        antialias: true,
        alpha: true
    });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 5;
    
    // Create stars
    const starsGeometry = new THREE.BufferGeometry();
    const starsMaterial = new THREE.PointsMaterial({
        color: 0xffffff,
        size: 0.1,
        transparent: true
    });
    
    const starsVertices = [];
    for (let i = 0; i < 2000; i++) {
        const x = (Math.random() - 0.5) * 2000;
        const y = (Math.random() - 0.5) * 2000;
        const z = (Math.random() - 0.5) * 2000;
        starsVertices.push(x, y, z);
    }
    
    starsGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starsVertices, 3));
    const stars = new THREE.Points(starsGeometry, starsMaterial);
    scene.add(stars);
    
    // Create nebula
    const nebulaGeometry = new THREE.SphereGeometry(400, 32, 32);
    const nebulaMaterial = new THREE.MeshBasicMaterial({
        color: 0x3d5afe,
        transparent: true,
        opacity: 0.03
    });
    const nebula = new THREE.Mesh(nebulaGeometry, nebulaMaterial);
    scene.add(nebula);
    
    // Animation
    function animate() {
        requestAnimationFrame(animate);
        
        stars.rotation.y += 0.0001;
        stars.rotation.z += 0.0001;
        
        nebula.rotation.y += 0.0002;
        
        renderer.render(scene, camera);
    }
    
    // Handle resize
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
    
    animate();
}

// Initialize GSAP animations
function initAnimations() {
    // Animate feature cards on scroll
    gsap.registerPlugin(ScrollTrigger);
    
    gsap.utils.toArray('.feature-card').forEach((card, i) => {
        gsap.from(card, {
            y: 100,
            opacity: 0,
            duration: 1,
            delay: i * 0.2,
            scrollTrigger: {
                trigger: card,
                start: 'top bottom-=100',
                toggleActions: 'play none none none'
            }
        });
    });
    
    // Animate section header
    gsap.from('.section-title', {
        y: -50,
        opacity: 0,
        duration: 1,
        scrollTrigger: {
            trigger: '.section-header',
            start: 'top bottom-=100',
            toggleActions: 'play none none none'
        }
    });
    
    gsap.from('.section-subtitle', {
        y: 50,
        opacity: 0,
        duration: 1,
        delay: 0.3,
        scrollTrigger: {
            trigger: '.section-header',
            start: 'top bottom-=100',
            toggleActions: 'play none none none'
        }
    });
    
    // Stats counter animation
    const statValues = document.querySelectorAll('.stat-value');
    
    statValues.forEach(statValue => {
        const finalValue = parseInt(statValue.getAttribute('data-count'));
        
        gsap.to(statValue, {
            innerHTML: finalValue,
            duration: 2,
            ease: 'power2.out',
            snap: { innerHTML: 1 },
            scrollTrigger: {
                trigger: statValue,
                start: 'top bottom-=100',
                toggleActions: 'play none none none'
            },
            onUpdate: function() {
                statValue.innerHTML = Math.round(this.targets()[0].innerHTML);
            }
        });
    });
    
    // CTA buttons animation
    gsap.from('.cta-button', {
        y: 30,
        opacity: 0,
        duration: 1,
        stagger: 0.2,
        scrollTrigger: {
            trigger: '.cta-container',
            start: 'top bottom-=50',
            toggleActions: 'play none none none'
        }
    });
}

// Initialize Vanilla Tilt for 3D card effect
function initTilt() {
    VanillaTilt.init(document.querySelectorAll('.feature-card'), {
        max: 10,
        speed: 400,
        glare: true,
        'max-glare': 0.3,
        gyroscope: true
    });
}

// Initialize everything when the page loads
window.addEventListener('DOMContentLoaded', () => {
    initCosmicBackground();
    initAnimations();
    initTilt();
});

// Student Showcase
// Intersection Observer for card animations
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.student-card');
    const title = document.querySelector('.showcase-title');
    let currentCardIndex = 0;
    
    // Initial animation for title
    setTimeout(() => {
        title.style.animation = 'fadeInDown 1s forwards';
    }, 300);
    
    // Function to check if element is in viewport
    const isInViewport = (element) => {
        const rect = element.getBoundingClientRect();
        return (
            rect.top <= (window.innerHeight || document.documentElement.clientHeight) * 0.8 &&
            rect.bottom >= 0
        );
    };
    
    // Animate cards sequentially when in viewport
    const animateCards = () => {
        cards.forEach((card, index) => {
            if (isInViewport(card) && !card.classList.contains('active-card')) {
                setTimeout(() => {
                    card.classList.add('active-card');
                    if (index % 2 === 0) {
                        card.style.animation = 'fadeInLeft 0.8s forwards';
                    } else {
                        card.style.animation = 'fadeInRight 0.8s forwards';
                    }
                }, index * 300);
            }
        });
    };
    
    // Auto-rotate cards for carousel effect
    const rotateCards = () => {
        cards.forEach(card => card.classList.remove('active-card'));
        currentCardIndex = (currentCardIndex + 1) % cards.length;
        cards[currentCardIndex].classList.add('active-card');
    };
    
    // Add scrolling event listener
    window.addEventListener('scroll', animateCards);
    
    // Initial check for visible cards
    animateCards();
    
    // Set up automatic card rotation every 5 seconds
    setInterval(() => {
        if (!isInViewport(cards[0])) return; // Only auto-rotate when in viewport
        rotateCards();
    }, 5000);
});

document.addEventListener('DOMContentLoaded', function() {
    // Функционал вкладок
    const tabs = document.querySelectorAll('.tab-button');
    const branchCards = document.querySelectorAll('.branch-card');

    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Удаляем активный класс у всех вкладок
            tabs.forEach(t => t.classList.remove('active'));
            
            // Добавляем активный класс нажатой вкладке
            this.classList.add('active');
            
            // Получаем выбранный регион
            const selectedRegion = this.getAttribute('data-region');
            
            // Показываем/скрываем карточки филиалов
            branchCards.forEach(card => {
                // Сбрасываем анимацию
                card.style.animation = 'none';
                card.offsetHeight; // Триггерит перерисовку

                if (selectedRegion === 'all' || card.getAttribute('data-region') === selectedRegion) {
                    card.style.display = 'block';
                    // Восстанавливаем анимацию
                    card.style.animation = 'fadeInUp 0.8s forwards';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });

    // Анимация при скролле
    const animateOnScroll = () => {
        const elements = document.querySelectorAll('.branch-card, .map-section');
        
        elements.forEach(el => {
            const rect = el.getBoundingClientRect();
            const isVisible = (rect.top <= (window.innerHeight || document.documentElement.clientHeight) * 0.85);
            
            if (isVisible && el.style.display !== 'none') {
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }
        });
    };

    // Вызываем функцию при загрузке и скролле
    window.addEventListener('scroll', animateOnScroll);
    animateOnScroll(); // Проверяем при загрузке
});

// Функция для инициализации Яндекс карты
let map;
let placemark;

function initMap() {
    // Создаем карту
    map = new ymaps.Map('map', {
        center: [41.311151, 69.279737], // Координаты центра Ташкента
        zoom: 12,
        controls: ['zoomControl', 'fullscreenControl']
    });

    // Добавляем все филиалы на карту
    addAllBranches();
}

function addAllBranches() {
    const branches = document.querySelectorAll('.branch-button');
    
    branches.forEach(branch => {
        const lat = parseFloat(branch.getAttribute('data-lat'));
        const lng = parseFloat(branch.getAttribute('data-lng'));
        const name = branch.closest('.branch-card').querySelector('.branch-name').textContent;
        const address = branch.closest('.branch-card').querySelector('.branch-address').textContent;
        
        const placemark = new ymaps.Placemark([lat, lng], {
            balloonContent: `<strong>${name}</strong><br>${address}`
        }, {
            preset: 'islands#blueEducationIcon'
        });
        
        map.geoObjects.add(placemark);
    });
}

function showOnMap(button) {
    const lat = parseFloat(button.getAttribute('data-lat'));
    const lng = parseFloat(button.getAttribute('data-lng'));
    const name = button.closest('.branch-card').querySelector('.branch-name').textContent;
    const address = button.closest('.branch-card').querySelector('.branch-address').textContent;
    
    // Центрируем карту на выбранном филиале
    map.setCenter([lat, lng], 16, {
        duration: 500
    });
    
    // Открываем балун с информацией
    map.balloon.open([lat, lng], {
        contentHeader: name,
        contentBody: address
    });
    
    // Скроллим к карте
    document.querySelector('.map-section').scrollIntoView({
        behavior: 'smooth'
    });
}

// Contact Section
// Инициализация карты
function init() {
    // Создаем карту
    var myMap = new ymaps.Map("map", {
      center: [55.751244, 37.618423],
      zoom: 12,
      controls: ['zoomControl', 'geolocationControl']
    });
    
    // Добавляем метки для всех филиалов
    var branches = document.querySelectorAll('.branch-item');
    var placemarks = [];
    
    branches.forEach(function(branch) {
      var coords = branch.dataset.coordinates.split(',').map(Number);
      var title = branch.querySelector('.branch-title').textContent;
      var address = branch.querySelector('.branch-address').textContent;
      
      var placemark = new ymaps.Placemark(coords, {
        balloonContent: '<strong>' + title + '</strong><br>' + address
      }, {
        preset: 'islands#blueIcon'
      });
      
      placemarks.push(placemark);
      myMap.geoObjects.add(placemark);
    });
    
    // Обработка клика по филиалу
    branches.forEach(function(branch, index) {
      branch.addEventListener('click', function() {
        // Меняем активный филиал
        document.querySelector('.active-branch').classList.remove('active-branch');
        this.classList.add('active-branch');
        
        // Перемещаем карту к выбранному филиалу
        var coords = this.dataset.coordinates.split(',').map(Number);
        myMap.setCenter(coords, 15);
        
        // Открываем балун
        placemarks[index].balloon.open();
      });
    });
  }
  
  // Загружаем API Яндекс Карт
  ymaps.ready(init);
  
  // Анимация при скролле
  document.addEventListener('DOMContentLoaded', function() {
    // Добавляем анимацию для элементов при прокрутке
    function animateOnScroll() {
      const elements = document.querySelectorAll('.branch-item');
      elements.forEach((el, index) => {
        setTimeout(() => {
          el.style.opacity = '0';
          el.style.transform = 'translateX(-20px)';
          el.style.transition = 'all 0.5s ease';
          
          setTimeout(() => {
            el.style.opacity = '1';
            el.style.transform = 'translateX(0)';
          }, 100 * index);
        }, 500);
      });
    }
    
    // Запускаем анимацию после загрузки страницы
    setTimeout(animateOnScroll, 1000);
  });

