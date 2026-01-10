// Attendance System JavaScript

$(document).ready(function() {
    // Auto-update current time in footer
    function updateTime() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        const dateStr = now.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        $('.current-time').remove();
        $('footer .container').append(
            `<p class="current-time small text-muted mb-0">${dateStr} | ${timeStr}</p>`
        );
    }
    
    // Update time every second
    updateTime();
    setInterval(updateTime, 1000);
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);
    
    // Prevent form resubmission on page refresh
    if (window.history.replaceState) {
        window.history.replaceState(null, null, window.location.href);
    }
    
    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Auto-focus first input in modals
    $('.modal').on('shown.bs.modal', function() {
        $(this).find('input[type="text"]:first, input[type="email"]:first').focus();
    });
    
    // ============ SMART FORM HANDLING ============
    let formChanged = false;
    let formSubmitClicked = false;
    
    // Track form changes (but not for empty forms)
    $('form input, form select, form textarea').on('change input', function() {
        const value = $(this).val();
        const defaultValue = $(this).attr('placeholder') || '';
        
        // Only mark as changed if there's real data
        if (value && value.trim() !== '' && value !== defaultValue) {
            formChanged = true;
            console.log('Form data changed');
        }
    });
    
    // Clear flag when form is submitted
    $('form').on('submit', function() {
        formSubmitClicked = true;
        formChanged = false;
        console.log('Form submitted - clearing warning flag');
        return true;
    });
    
    // Handle navigation clicks
    $('a.btn, button[type="submit"], .nav-link').on('click', function() {
        formSubmitClicked = true;
        formChanged = false;
    });
    
    // Smart beforeunload handler
    $(window).on('beforeunload', function(e) {
        // Don't show warning if form was submitted
        if (formSubmitClicked) {
            return undefined;
        }
        
        // Only show warning if there are real changes
        if (formChanged) {
            e.preventDefault();
            e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
            return e.returnValue;
        }
        
        return undefined;
    });
    
    // Auto-clear form change flag after delay
    let formChangeTimer;
    $('form input, form select, form textarea').on('change input', function() {
        clearTimeout(formChangeTimer);
        formChangeTimer = setTimeout(function() {
            formChanged = false;
            console.log('Form change flag auto-cleared (30s inactivity)');
        }, 30000);
    });
    
    // ============ FORM AUTO-SAVE FEATURE ============
    function setupFormAutoSave() {
        // Check for forms that should auto-save
        $('form').each(function() {
            const form = this;
            const formId = form.id || `form_${Date.now()}`;
            let autoSaveTimer;
            
            // Save form data on change
            $(form).find('input, select, textarea').on('change input', function() {
                clearTimeout(autoSaveTimer);
                
                autoSaveTimer = setTimeout(() => {
                    try {
                        const formData = new FormData(form);
                        const data = {};
                        
                        formData.forEach((value, key) => {
                            if (value && value.trim() !== '') {
                                data[key] = value;
                            }
                        });
                        
                        // Only save if there's data
                        if (Object.keys(data).length > 0) {
                            localStorage.setItem(`autoSave_${formId}`, JSON.stringify(data));
                            localStorage.setItem(`autoSave_${formId}_time`, new Date().toISOString());
                            
                            // Show subtle indicator
                            const indicator = $(`#autoSaveIndicator_${formId}`);
                            if (indicator.length === 0) {
                                $(form).append(`
                                    <div id="autoSaveIndicator_${formId}" class="auto-save-indicator">
                                        <small class="text-muted"><i class="fas fa-save"></i> Auto-saved</small>
                                    </div>
                                `);
                                setTimeout(() => $(`#autoSaveIndicator_${formId}`).fadeOut(1000), 2000);
                            }
                        }
                    } catch (e) {
                        console.error('Auto-save error:', e);
                    }
                }, 1500); // 1.5 second delay
            });
            
            // Load auto-saved data
            try {
                const savedData = localStorage.getItem(`autoSave_${formId}`);
                if (savedData) {
                    const data = JSON.parse(savedData);
                    Object.keys(data).forEach(key => {
                        const element = form.querySelector(`[name="${key}"]`);
                        if (element && !element.value) {
                            element.value = data[key];
                        }
                    });
                }
            } catch (e) {
                console.error('Error loading auto-saved data:', e);
            }
            
            // Clear on submit
            $(form).on('submit', function() {
                localStorage.removeItem(`autoSave_${formId}`);
                localStorage.removeItem(`autoSave_${formId}_time`);
            });
        });
    }
    
    // Initialize auto-save
    setupFormAutoSave();
    
    // ============ SUBMIT BUTTON LOADING STATE ============
    $('form').on('submit', function() {
        const submitBtn = $(this).find('button[type="submit"]');
        if (submitBtn.length) {
            submitBtn.prop('disabled', true);
            const originalHtml = submitBtn.html();
            submitBtn.html('<i class="fas fa-spinner fa-spin"></i> Processing...');
            
            // Re-enable button after 10 seconds (safety)
            setTimeout(() => {
                submitBtn.prop('disabled', false);
                submitBtn.html(originalHtml);
            }, 10000);
        }
    });
    
    // ============ BULK ACTION HANDLERS ============
    // Mark all present/absent in attendance page
    window.markAll = function(status) {
        if (confirm(`Mark ALL employees as ${status}?`)) {
            $('.status-select').each(function() {
                $(this).val(status).trigger('change');
                // Auto-save each row
                const empId = $(this).data('emp-id');
                if (empId && window.markAttendance) {
                    setTimeout(() => window.markAttendance(empId), 100);
                }
            });
        }
    };
    
    // ============ REAL-TIME VALIDATION ============
    $('input[required], select[required]').on('blur', function() {
        const value = $(this).val();
        if (!value || value.trim() === '') {
            $(this).addClass('is-invalid');
            $(this).after('<div class="invalid-feedback">This field is required</div>');
        } else {
            $(this).removeClass('is-invalid');
            $(this).next('.invalid-feedback').remove();
        }
    });
    
    // ============ SEARCH FUNCTIONALITY ============
    $('#searchEmployee').on('keyup', function() {
        const value = $(this).val().toLowerCase();
        $('table tbody tr').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
    });
});

// ============ UTILITY FUNCTIONS ============

function formatDate(date) {
    const d = new Date(date);
    return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatTime(date) {
    const d = new Date(date);
    return d.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ============ NOTIFICATION SYSTEM ============
function showNotification(message, type = 'info') {
    const types = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    };
    
    const icon = {
        'success': 'fa-check-circle',
        'error': 'fa-times-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    
    const toastId = 'toast_' + Date.now();
    const toast = `
        <div id="${toastId}" class="position-fixed top-0 end-0 p-3" style="z-index: 1060">
            <div class="toast align-items-center text-white ${types[type]} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="fas ${icon[type]} me-2"></i> ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                            data-bs-dismiss="toast"></button>
                </div>
            </div>
        </div>
    `;
    
    $('body').append(toast);
    $(`#${toastId} .toast`).toast('show');
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        $(`#${toastId}`).remove();
    }, 4000);
}

function downloadFile(filename, content, type = 'text/plain') {
    const blob = new Blob([content], { type: type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ============ EMPLOYEE MANAGEMENT FUNCTIONS ============

// Load employee for editing
function loadEmployeeForEdit(employeeId) {
    // Show loading state on the button
    const editBtn = $(`#emp-row-${employeeId} .btn-outline-primary`);
    const originalHtml = editBtn.html();
    editBtn.html('<i class="fas fa-spinner fa-spin"></i>');
    editBtn.prop('disabled', true);
    
    // Fetch employee data
    $.ajax({
        url: `/get_employee/${employeeId}`,
        type: 'GET',
        success: function(response) {
            if (response.success) {
                // Fill the edit form
                $('#editEmployeeId').val(response.employee.id);
                $('#editName').val(response.employee.name);
                $('#editEmployeeCode').val(response.employee.employee_id);
                $('#editDepartment').val(response.employee.department);
                $('#editPosition').val(response.employee.position);
                $('#editEmail').val(response.employee.email);
                $('#editPhone').val(response.employee.phone);
                $('#editJoinDate').val(response.employee.join_date);
                $('#editStatus').val(response.employee.status || 'active');
                
                // Show edit modal
                $('#editEmployeeModal').modal('show');
                
                // Show success notification
                showNotification('Employee details loaded successfully!', 'success');
            } else {
                showNotification(response.message || 'Failed to load employee details', 'error');
            }
        },
        error: function(xhr, status, error) {
            showNotification('Error loading employee details: ' + error, 'error');
        },
        complete: function() {
            // Restore button state
            editBtn.html(originalHtml);
            editBtn.prop('disabled', false);
        }
    });
}

// Confirm delete employee (with modal version)
function confirmDelete(empId, empName) {
    $('#deleteEmpName').text(empName);
    $('#confirmDeleteBtn').attr('href', '/delete_employee/' + empId);
    $('#deleteModal').modal('show');
}

// Simple confirm delete (alert version)
function simpleConfirmDelete(empId, empName) {
    if (confirm(`Are you sure you want to delete employee: ${empName}?\nThis action cannot be undone!`)) {
        window.location.href = `/delete_employee/${empId}`;
    }
}

// ============ ATTENDANCE FUNCTIONS ============
function markAttendance(empId) {
    const status = $(`select[data-emp-id="${empId}"]`).val();
    const notes = $(`input[data-emp-id="${empId}"]`).val();
    const date = $(`input[name="date"]`).val() || new Date().toISOString().split('T')[0];
    
    if (!status) {
        showNotification('Please select a status first!', 'warning');
        return;
    }
    
    // Disable button and show loading
    const btn = $(`.mark-btn[data-emp-id="${empId}"]`);
    const originalHtml = btn.html();
    btn.html('<i class="fas fa-spinner fa-spin"></i> Saving...');
    btn.prop('disabled', true);
    
    // Send AJAX request
    $.ajax({
        url: '/mark_attendance',
        type: 'POST',
        data: {
            employee_id: empId,
            status: status,
            date: date,
            notes: notes
        },
        success: function(response) {
            if (response.success) {
                // Show success
                const row = $('#row-' + empId);
                row.removeClass('table-danger table-warning').addClass('table-success');
                
                // Update button
                btn.removeClass('btn-primary').addClass('btn-success');
                btn.html('<i class="fas fa-check"></i> Saved');
                btn.prop('disabled', true);
                
                // Show notification
                showNotification(response.message, 'success');
                
                // Update stats if function exists
                if (typeof updateStats === 'function') {
                    updateStats();
                }
            } else {
                showNotification(response.message, 'error');
                btn.html(originalHtml);
                btn.prop('disabled', false);
            }
        },
        error: function() {
            showNotification('Error saving attendance!', 'error');
            btn.html(originalHtml);
            btn.prop('disabled', false);
        }
    });
}

// ============ FORM HANDLING FUNCTIONS ============
function setupFormSubmission(formId) {
    $(`#${formId}`).on('submit', function(e) {
        e.preventDefault();
        
        const form = this;
        const submitBtn = $(form).find('button[type="submit"]');
        const originalHtml = submitBtn.html();
        
        // Disable and show loading
        submitBtn.prop('disabled', true);
        submitBtn.html('<i class="fas fa-spinner fa-spin"></i> Processing...');
        
        // Collect form data
        const formData = new FormData(form);
        const data = {};
        formData.forEach((value, key) => {
            data[key] = value;
        });
        
        // Send request
        $.ajax({
            url: form.action,
            type: form.method,
            data: data,
            success: function(response) {
                if (response.success) {
                    showNotification(response.message, 'success');
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    showNotification(response.message, 'error');
                    submitBtn.html(originalHtml);
                    submitBtn.prop('disabled', false);
                }
            },
            error: function() {
                showNotification('Request failed. Please try again.', 'error');
                submitBtn.html(originalHtml);
                submitBtn.prop('disabled', false);
            }
        });
    });
}

// ============ GLOBAL ERROR HANDLER ============
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showNotification('An error occurred. Please try again.', 'error');
});

// ============ OFFLINE DETECTION ============
window.addEventListener('online', function() {
    showNotification('You are back online!', 'success');
});

window.addEventListener('offline', function() {
    showNotification('You are offline. Some features may not work.', 'warning');
});

// ============ INITIALIZATION FUNCTIONS ============
function initDatePickers() {
    // Initialize date pickers with today's date
    $('input[type="date"]').each(function() {
        if (!$(this).val()) {
            const today = new Date().toISOString().split('T')[0];
            $(this).val(today);
        }
    });
}

function initDataTables() {
    // Simple table sorting
    $('table th').click(function() {
        const table = $(this).parents('table').eq(0);
        const rows = table.find('tr:gt(0)').toArray().sort(comparer($(this).index()));
        this.asc = !this.asc;
        if (!this.asc) {
            rows = rows.reverse();
        }
        for (let i = 0; i < rows.length; i++) {
            table.append(rows[i]);
        }
    });
    
    function comparer(index) {
        return function(a, b) {
            const valA = $(a).children('td').eq(index).text();
            const valB = $(b).children('td').eq(index).text();
            return $.isNumeric(valA) && $.isNumeric(valB) ? 
                valA - valB : valA.toString().localeCompare(valB);
        };
    }
}

// Initialize on page load
$(document).ready(function() {
    initDatePickers();
    initDataTables();
    
    // Set up form submissions
    if ($('#addEmployeeForm').length) setupFormSubmission('addEmployeeForm');
    if ($('#editEmployeeForm').length) setupFormSubmission('editEmployeeForm');
    
    // Auto-refresh dashboard data every 60 seconds
    if (window.location.pathname === '/dashboard') {
        setInterval(() => {
            if (typeof loadAttendanceChart === 'function') {
                loadAttendanceChart();
            }
        }, 60000);
    }
});