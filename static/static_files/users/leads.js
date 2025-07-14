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

    // --- Trello-like Drag&Drop между секциями внутри колонок ---
    const sectionLeadsContainers = Array.from(document.querySelectorAll('.section-leads'));
    if (sectionLeadsContainers.length > 0 && window.dragula) {
        const drake = dragula(sectionLeadsContainers, {
            moves: function(el, container, handle) {
                return handle.classList.contains('drag-handle');
            }
        });

        // Определяем колонку по родителю
        function getColumnBySection(sectionEl) {
            let parent = sectionEl;
            while (parent && !parent.id?.match(/^(new|waiting|trial|attending)-leads-container$/)) {
                parent = parent.parentElement;
            }
            if (!parent) return null;
            if (parent.id.startsWith('new')) return 'new';
            if (parent.id.startsWith('waiting')) return 'waiting';
            if (parent.id.startsWith('trial')) return 'trial';
            if (parent.id.startsWith('attending')) return 'attending';
            return null;
        }

        drake.on('drop', function(el, target, source, sibling) {
            const leadId = el.getAttribute('data-lead-id');
            const newSectionId = target.closest('.section-header')?.getAttribute('data-section-id') || null;
            const newColumn = getColumnBySection(target);

            // Определяем новый порядок
            let siblings = Array.from(target.children).filter(child => child.classList.contains('kanban-item'));
            let newOrder = siblings.indexOf(el) + 1;

            // Обновляем визуально
            el.setAttribute('data-order', newOrder);

            // CSRF
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;

            // Отправляем на сервер
            fetch('/student-tracking/move-lead/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    leadId: leadId,
                    newColumn: newColumn,
                    newOrder: newOrder,
                    newSectionId: newSectionId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Можно обновить счетчики, если нужно
                    // updateCounters();
                    console.log('Lead moved successfully');
                } else {
                    console.error('Error moving lead:', data.message);
                    drake.cancel(true);
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
                drake.cancel(true);
            });
        });
    }
    // --- END Trello-like Drag&Drop ---
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

// Function to update the lead status
document.addEventListener('DOMContentLoaded', function() {
    // Initialize dragula
    const containers = [
        document.getElementById('new-leads-container'),
        document.getElementById('waiting-leads-container'),
        document.getElementById('trial-leads-container'),
        document.getElementById('attending-leads-container')
    ];
    
    const drake = dragula(containers, {
        moves: function(el, container, handle) {
            return handle.classList.contains('drag-handle');
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
        let newOrder = 1;
        if (sibling) {
            const siblingOrder = parseInt(sibling.getAttribute('data-order') || '0');
            newOrder = siblingOrder;
        } else {
            // If dropped at the end
            const allCards = target.querySelectorAll('.kanban-item');
            if (allCards.length > 1) {
                const lastCard = allCards[allCards.length - 2]; // -2 because the current card is already in the container
                const lastOrder = parseInt(lastCard.getAttribute('data-order') || '0');
                newOrder = lastOrder + 1;
            }
        }
        
        // Update the card visually
        el.setAttribute('data-order', newOrder);
        
        // Update the counter
        updateCounters();
        
        // Send the update to the server
        fetch('{% url "move_lead" %}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
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
    
    // Function to update counters
    function updateCounters() {
        const newCount = document.getElementById('new-leads-container').querySelectorAll('.kanban-item').length;
        const waitingCount = document.getElementById('waiting-leads-container').querySelectorAll('.kanban-item').length;
        const trialCount = document.getElementById('trial-leads-container').querySelectorAll('.kanban-item').length;
        const attendingCount = document.getElementById('attending-leads-container').querySelectorAll('.kanban-item').length;
        
        document.querySelector('.bg-primary .badge').textContent = newCount;
        document.querySelector('.bg-warning .badge').textContent = waitingCount;
        document.querySelector('.bg-info .badge').textContent = trialCount;
        document.querySelector('.bg-success .badge').textContent = attendingCount;
    }
    
    // Add Section Modal - Update column field when opened
    const addSectionModal = document.getElementById('addSectionModal');
    if (addSectionModal) {
        addSectionModal.addEventListener('shown.bs.modal', function(event) {
            const button = event.relatedTarget;
            const column = button.getAttribute('data-column');
            if (column) {
                document.getElementById('id_section_column').value = column;
            }
        });
    }
    
    // Course-Branch filtering
    const courseSelect = document.getElementById('id_course');
    const branchSelect = document.getElementById('id_branch');
    
    if (courseSelect && branchSelect) {
        courseSelect.addEventListener('change', function() {
            const courseId = this.value;
            
            // Reset branch select
            for (const option of branchSelect.options) {
                if (option.value === '') {
                    option.selected = true;
                } else {
                    const optionCourseId = option.getAttribute('data-course');
                    
                    if (courseId === '' || optionCourseId === courseId) {
                        option.style.display = '';
                    } else {
                        option.style.display = 'none';
                    }
                }
            }
        });
    }
    
    // Обработка добавления нового источника
    const addSourceForm = document.getElementById('addSourceForm');
    if (addSourceForm) {
        addSourceForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            fetch(this.action, {
                method: 'POST',
                body: new FormData(this),
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Добавляем новый источник в select
                    const sourceSelect = document.getElementById('id_source');
                    const option = new Option(data.source.name, data.source.id);
                    sourceSelect.add(option);
                    sourceSelect.value = data.source.id;
                    
                    // Закрываем модальное окно
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addSourceModal'));
                    modal.hide();
                    
                    // Очищаем форму
                    this.reset();
                    
                    // Показываем сообщение об успехе
                    alert(data.message);
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Произошла ошибка при добавлении источника');
            });
        });
    }
});