/**
 * Main JavaScript for Student Tracking System
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize all popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto close alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Phone number formatter
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 0) {
                if (value.length <= 3) {
                    value = '+' + value;
                } else if (value.length <= 6) {
                    value = '+' + value.substring(0, 3) + ' ' + value.substring(3);
                } else if (value.length <= 9) {
                    value = '+' + value.substring(0, 3) + ' ' + value.substring(3, 6) + ' ' + value.substring(6);
                } else {
                    value = '+' + value.substring(0, 3) + ' ' + value.substring(3, 6) + ' ' + value.substring(6, 9) + ' ' + value.substring(9);
                }
            }
            e.target.value = value;
        });
    });

    // Add animation classes to elements
    const animationElements = document.querySelectorAll('.card, .alert, .btn-primary');
    animationElements.forEach(function(element) {
        element.classList.add('fade-in');
    });

    // Filter branch options based on selected course
    const courseSelect = document.getElementById('id_course');
    const branchSelect = document.getElementById('id_branch');
    
    if (courseSelect && branchSelect) {
        courseSelect.addEventListener('change', function() {
            const courseId = this.value;
            
            // Hide all branch options
            Array.from(branchSelect.options).forEach(function(option) {
                if (option.value === '') {
                    // Don't hide the placeholder option
                    return;
                }
                
                const optionCourseId = option.getAttribute('data-course');
                if (!courseId || optionCourseId === courseId) {
                    option.style.display = '';
                } else {
                    option.style.display = 'none';
                }
            });
            
            // Reset branch selection
            branchSelect.value = '';
        });
    }
    
    // Time validation for group scheduling
    const startTimeInput = document.getElementById('id_start_time');
    const endTimeInput = document.getElementById('id_end_time');
    
    if (startTimeInput && endTimeInput) {
        // Ensure end time is after start time
        endTimeInput.addEventListener('change', function() {
            const startTime = startTimeInput.value;
            const endTime = this.value;
            
            if (startTime && endTime && startTime >= endTime) {
                alert('Время окончания должно быть позже времени начала');
                this.value = '';
            }
        });
        
        startTimeInput.addEventListener('change', function() {
            const startTime = this.value;
            const endTime = endTimeInput.value;
            
            if (startTime && endTime && startTime >= endTime) {
                endTimeInput.value = '';
            }
        });
    }
    
    // Add section modal - update column field when opened
    const addSectionModal = document.getElementById('addSectionModal');
    if (addSectionModal) {
        addSectionModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const column = button.getAttribute('data-column');
            
            if (column) {
                document.getElementById('id_section_column').value = column;
            }
        });
    }
    
    // Search functionality
    const searchInput = document.getElementById('id_search');
    if (searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.closest('form').submit();
            }
        });
    }

    // Kanban drag and drop functionality with Dragula
    const containers = document.querySelectorAll('.kanban-items');
    if (containers.length > 0 && window.dragula) {
        const drake = dragula(Array.from(containers), {
            moves: function(el, container, handle) {
                return handle.classList.contains('drag-handle') || el.querySelector('.drag-handle');
            },
            accepts: function(el, target, source, sibling) {
                // Don't allow drops if the card is being dragged over itself
                if (sibling === el) {
                    return false;
                }
                return true;
            }
        });
        
        // Column IDs to board_column values mapping
        const columnMap = {
            'new-leads-container': 'new',
            'waiting-leads-container': 'waiting',
            'trial-leads-container': 'trial',
            'attending-leads-container': 'attending'
        };
        
        // When a lead is dropped
        drake.on('drop', function(el, target, source, sibling) {
            const leadId = el.getAttribute('data-lead-id');
            const newColumn = columnMap[target.id];
            
            // Calculate new order
            let siblings = Array.from(target.children);
            let newOrder = siblings.indexOf(el) + 1;
            
            // Update the card visually
            el.setAttribute('data-order', newOrder);
            
            // Get CSRF token
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                             document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
            
            // Send the update to the server
            fetch('/student-tracking/move-lead/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    leadId: leadId,
                    newColumn: newColumn,
                    newOrder: newOrder
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Update counters
                    updateCounters();
                    console.log('Lead moved successfully');
                } else {
                    console.error('Error moving lead:', data.message);
                    // Revert the drag if there was an error
                    drake.cancel(true);
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
                drake.cancel(true);
            });
        });
    }
    
    // Function to update counters
    function updateCounters() {
        const columns = ['new', 'waiting', 'trial', 'attending'];
        const colorMap = {
            'new': 'primary',
            'waiting': 'warning',
            'trial': 'info',
            'attending': 'success'
        };
        
        columns.forEach(column => {
            const container = document.getElementById(`${column}-leads-container`);
            if (container) {
                const count = container.querySelectorAll('.kanban-item').length;
                const badge = document.querySelector(`.bg-${colorMap[column]} .badge`);
                if (badge) {
                    badge.textContent = count;
                }
            }
        });
    }
});

// Mobile menu toggling
document.addEventListener('click', function(e) {
    const dropdown = e.target.closest('.dropdown');
    if (!dropdown) return;
    
    const menu = dropdown.querySelector('.dropdown-menu');
    if (!menu) return;
    
    // Close other open menus
    document.querySelectorAll('.dropdown-menu.show').forEach(function(openMenu) {
        if (openMenu !== menu) {
            openMenu.classList.remove('show');
        }
    });
});

// Helper function to format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// Helper function to format time
function formatTime(timeString) {
    const [hours, minutes] = timeString.split(':');
    return `${hours}:${minutes}`;
}

// Confirm delete action
function confirmDelete(message = 'Вы уверены, что хотите удалить этот элемент?') {
    return confirm(message);
}