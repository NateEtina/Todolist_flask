document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Task completion toggle with AJAX
    const taskCheckboxes = document.querySelectorAll('.task-complete');
    taskCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const taskItem = this.closest('.task-item');
            const taskId = taskItem.dataset.taskId;
            
            // Add loading state
            this.disabled = true;
            this.closest('.form-check').innerHTML += 
                '<span class="spinner-border spinner-border-sm ms-2" role="status"></span>';
            
            fetch(`/task/${taskId}/complete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'completed' || data.status === 'pending') {
                    // Update UI
                    const title = taskItem.querySelector('h5');
                    title.classList.toggle('text-decoration-line-through');
                    title.classList.toggle('text-muted');
                    
                    // Show success feedback
                    showNotification('Task updated successfully!', 'success');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Error updating task', 'danger');
                // Revert checkbox state
                this.checked = !this.checked;
            })
            .finally(() => {
                // Remove loading state
                this.disabled = false;
                const spinner = this.closest('.form-check').querySelector('.spinner-border');
                if (spinner) spinner.remove();
            });
        });
    });

    // Delete task with confirmation
    const deleteButtons = document.querySelectorAll('.delete-task');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const taskId = this.dataset.taskId;
            const taskItem = this.closest('.task-item');
            
            // Show confirmation dialog
            if (!confirm('Are you sure you want to delete this task?')) {
                return;
            }
            
            // Disable button and show loading
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';
            
            fetch(`/task/${taskId}/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                // Remove task from DOM with animation
                taskItem.style.transition = 'all 0.3s ease';
                taskItem.style.opacity = '0';
                taskItem.style.transform = 'translateX(100px)';
                setTimeout(() => {
                    taskItem.remove();
                    showNotification('Task deleted successfully!', 'success');
                    
                    // Update statistics if visible
                    updateStatistics();
                }, 300);
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Error deleting task', 'danger');
                this.disabled = false;
                this.innerHTML = '<i class="fas fa-trash"></i> Delete';
            });
        });
    });

    // Filter buttons active state
    const filterButtons = document.querySelectorAll('.btn-group .btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            filterButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Notification system
    function showNotification(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        
        const iconMap = {
            'success': 'check-circle',
            'danger': 'exclamation-circle',
            'warning': 'warning',
            'info': 'info-circle'
        };
        
        alertDiv.innerHTML = `
            <i class="fas fa-${iconMap[type] || 'info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container');
        const firstChild = container.firstChild;
        container.insertBefore(alertDiv, firstChild);
        
        // Auto dismiss
        setTimeout(() => {
            if (alertDiv.parentNode) {
                const bsAlert = new bootstrap.Alert(alertDiv);
                bsAlert.close();
            }
        }, 5000);
    }

    // Update statistics
    function updateStatistics() {
        const taskItems = document.querySelectorAll('.task-item');
        const totalTasks = taskItems.length;
        const completedTasks = document.querySelectorAll('.task-complete:checked').length;
        const pendingTasks = totalTasks - completedTasks;
        
        // Update stat cards if they exist
        const statTotal = document.querySelector('.stat-card.bg-primary h3');
        const statCompleted = document.querySelector('.stat-card.bg-success h3');
        const statPending = document.querySelector('.stat-card.bg-warning h3');
        const statRate = document.querySelector('.stat-card.bg-info h3');
        
        if (statTotal) statTotal.textContent = totalTasks;
        if (statCompleted) statCompleted.textContent = completedTasks;
        if (statPending) statPending.textContent = pendingTasks;
        if (statRate) {
            const rate = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
            statRate.textContent = rate + '%';
        }
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+N for new task
        if (e.ctrlKey && e.key === 'n') {
            e.preventDefault();
            const newTaskBtn = document.querySelector('a[href*="task/new"]');
            if (newTaskBtn) window.location.href = newTaskBtn.href;
        }
    });

    // Smooth form submission feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Loading...';
            }
        });
    });

    console.log('TaskFlow App initialized successfully! 🚀');
});