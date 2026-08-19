from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.tasks import tasks_bp
from app.tasks.forms import TaskForm, ProjectForm
from app.models import Task, Project

@tasks_bp.route('/')
@tasks_bp.route('/dashboard')
@login_required
def dashboard():
    filter_type = request.args.get('filter', 'all')
    project_id = request.args.get('project', None)
    
    query = Task.query.filter_by(user_id=current_user.id)
    
    if project_id:
        query = query.filter_by(project_id=project_id)
    
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
    elif filter_type == 'blocked':
        # Tasks that are blocked by dependencies
        tasks = query.all()
        tasks = [t for t in tasks if t.is_blocked()]
        return render_template('tasks/dashboard.html', 
                             tasks=tasks, 
                             filter_type=filter_type,
                             projects=Project.query.filter_by(user_id=current_user.id).all())
    
    tasks = query.order_by(Task.created_at.desc()).all()
    
    # Statistics
    total_tasks = Task.query.filter_by(user_id=current_user.id).count()
    completed_tasks = Task.query.filter_by(user_id=current_user.id, completed=True).count()
    pending_tasks = total_tasks - completed_tasks
    blocked_tasks = len([t for t in Task.query.filter_by(user_id=current_user.id).all() if t.is_blocked()])
    
    projects = Project.query.filter_by(user_id=current_user.id).all()
    
    return render_template('tasks/dashboard.html', 
                         tasks=tasks, 
                         filter_type=filter_type,
                         total_tasks=total_tasks,
                         completed_tasks=completed_tasks,
                         pending_tasks=pending_tasks,
                         blocked_tasks=blocked_tasks,
                         projects=projects,
                         current_project=project_id)

@tasks_bp.route('/task/new', methods=['GET', 'POST'])
@login_required
def new_task():
    form = TaskForm()
    
    # Populate project choices
    user_projects = Project.query.filter_by(user_id=current_user.id).all()
    form.project_id.choices = [(0, 'No Project')] + [(p.id, p.name) for p in user_projects]
    
    # Populate dependency choices (only tasks that are not completed)
    existing_tasks = Task.query.filter_by(user_id=current_user.id, completed=False).all()
    form.depends_on_id.choices = [(0, 'No Dependency')] + [(t.id, f'{t.title}') for t in existing_tasks]
    
    # Set default values
    if request.method == 'GET':
        form.project_id.data = 0  # Default to 'No Project'
        form.depends_on_id.data = 0  # Default to 'No Dependency'
    
    if form.validate_on_submit():
        # Get project_id, default to None if 0
        project_id = form.project_id.data if form.project_id.data != 0 else None
        depends_on_id = form.depends_on_id.data if form.depends_on_id.data != 0 else None
        
        # Check if project exists and belongs to user
        if project_id:
            project = Project.query.get(project_id)
            if not project or project.user_id != current_user.id:
                flash('Invalid project selected.', 'danger')
                return render_template('tasks/edit_task.html', form=form, title='New Task')
        
        task = Task(
            title=form.title.data,
            description=form.description.data,
            priority=form.priority.data,
            due_date=form.due_date.data,
            reminder_date=form.reminder_date.data,
            user_id=current_user.id,
            project_id=project_id,
            depends_on_id=depends_on_id
        )
        db.session.add(task)
        db.session.commit()
        
        # Update project progress
        if task.project_id:
            project = Project.query.get(task.project_id)
            project.update_progress()
            
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
    
    # Populate project choices
    user_projects = Project.query.filter_by(user_id=current_user.id).all()
    form.project_id.choices = [(0, 'No Project')] + [(p.id, p.name) for p in user_projects]
    
    # Populate dependency choices (exclude current task)
    existing_tasks = Task.query.filter_by(user_id=current_user.id, completed=False).filter(Task.id != task.id).all()
    form.depends_on_id.choices = [(0, 'No Dependency')] + [(t.id, f'{t.title}') for t in existing_tasks]
    
    # Set current values
    if request.method == 'GET':
        form.project_id.data = task.project_id or 0
        form.depends_on_id.data = task.depends_on_id or 0
    
    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.priority = form.priority.data
        task.due_date = form.due_date.data
        task.reminder_date = form.reminder_date.data
        task.project_id = form.project_id.data if form.project_id.data != 0 else None
        task.depends_on_id = form.depends_on_id.data if form.depends_on_id.data != 0 else None
        db.session.commit()
        
        # Update project progress
        if task.project_id:
            project = Project.query.get(task.project_id)
            project.update_progress()
            
        flash('Task updated successfully!', 'success')
        return redirect(url_for('tasks.dashboard'))
    return render_template('tasks/edit_task.html', form=form, title='Edit Task', task=task)

@tasks_bp.route('/task/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if task can be completed (dependencies must be done)
    if not task.completed and not task.can_complete():
        blocking_tasks = task.get_blocking_tasks()
        blocking_names = ', '.join([t.title for t in blocking_tasks])
        return jsonify({
            'error': f'Task is blocked by: {blocking_names}',
            'blocked': True
        }), 400
    
    task.completed = not task.completed
    db.session.commit()
    
    # Update project progress
    if task.project_id:
        project = Project.query.get(task.project_id)
        project.update_progress()
    
    status = 'completed' if task.completed else 'pending'
    
    # Check if dependent tasks can now be unblocked
    unblocked_tasks = []
    if task.completed:
        for dependent in task.dependents:
            if dependent.is_blocked():
                unblocked_tasks.append(dependent.title)
    
    return jsonify({
        'status': status, 
        'message': 'Task updated successfully!',
        'unblocked': unblocked_tasks
    })

@tasks_bp.route('/projects')
@login_required
def projects():
    projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('tasks/projects.html', projects=projects)

@tasks_bp.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(
            name=form.name.data,
            description=form.description.data,
            color=form.color.data,
            user_id=current_user.id
        )
        db.session.add(project)
        db.session.commit()
        flash('Project created successfully!', 'success')
        return redirect(url_for('tasks.projects'))
    return render_template('tasks/edit_project.html', form=form, title='New Project')

@tasks_bp.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        flash('You do not have permission to edit this project.', 'danger')
        return redirect(url_for('tasks.projects'))
    
    form = ProjectForm(obj=project)
    if form.validate_on_submit():
        project.name = form.name.data
        project.description = form.description.data
        project.color = form.color.data
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('tasks.projects'))
    return render_template('tasks/edit_project.html', form=form, title='Edit Project', project=project)

@tasks_bp.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Move tasks to no project or delete them
    for task in project.tasks:
        task.project_id = None
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted successfully!'})
