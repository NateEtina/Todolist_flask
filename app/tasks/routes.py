from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.tasks import tasks_bp
from app.tasks.forms import TaskForm
from app.models import Task

@tasks_bp.route('/')
@tasks_bp.route('/dashboard')
@login_required
def dashboard():
    filter_type = request.args.get('filter', 'all')
    query = Task.query.filter_by(user_id=current_user.id)
    
    if filter_type == 'completed':
        query = query.filter_by(completed=True)
    elif filter_type == 'pending':
        query = query.filter_by(completed=False)
    elif filter_type == 'high':
        query = query.filter_by(priority='high')
    elif filter_type == 'medium':
        query = query.filter_by(priority='medium')
    elif filter_type == 'low':
        query = query.filter_by(priority='low')
    
    tasks = query.order_by(Task.created_at.desc()).all()
    
    # Statistics
    total_tasks = Task.query.filter_by(user_id=current_user.id).count()
    completed_tasks = Task.query.filter_by(user_id=current_user.id, completed=True).count()
    pending_tasks = total_tasks - completed_tasks
    
    return render_template('tasks/dashboard.html', 
                         tasks=tasks, 
                         filter_type=filter_type,
                         total_tasks=total_tasks,
                         completed_tasks=completed_tasks,
                         pending_tasks=pending_tasks)

@tasks_bp.route('/task/new', methods=['GET', 'POST'])
@login_required
def new_task():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            priority=form.priority.data,
            due_date=form.due_date.data,
            user_id=current_user.id
        )
        db.session.add(task)
        db.session.commit()
        flash('Task created successfully!', 'success')
        return redirect(url_for('tasks.dashboard'))
    return render_template('tasks/edit_task.html', form=form, title='New Task')

@tasks_bp.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('You do not have permission to edit this task.', 'danger')
        return redirect(url_for('tasks.dashboard'))
    
    form = TaskForm(obj=task)
    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.priority = form.priority.data
        task.due_date = form.due_date.data
        db.session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('tasks.dashboard'))
    return render_template('tasks/edit_task.html', form=form, title='Edit Task', task=task)

@tasks_bp.route('/task/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    task.completed = not task.completed
    db.session.commit()
    status = 'completed' if task.completed else 'pending'
    return jsonify({'status': status, 'message': 'Task updated successfully!'})

@tasks_bp.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted successfully!'})