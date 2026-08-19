from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')
    projects = db.relationship('Project', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(20), default='primary')
    progress = db.Column(db.Float, default=0.0)  # 0-100
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def update_progress(self):
        if not self.tasks:
            self.progress = 0.0
        else:
            completed = sum(1 for task in self.tasks if task.completed)
            self.progress = (completed / len(self.tasks)) * 100
        db.session.commit()
    
    def __repr__(self):
        return f'<Project {self.name}>'

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(20), default='medium')
    due_date = db.Column(db.DateTime)
    reminder_date = db.Column(db.DateTime)  # For reminders
    reminder_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    
    # Task Dependency - Sequential Tasks
    depends_on_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    depends_on = db.relationship('Task', remote_side=[id], backref='dependents')
    
    def is_blocked(self):
        """Check if task is blocked by dependencies"""
        if self.depends_on:
            return not self.depends_on.completed
        return False
    
    def can_complete(self):
        """Check if task can be completed (dependencies must be done)"""
        if self.depends_on:
            return self.depends_on.completed
        return True
    
    def get_blocking_tasks(self):
        """Get tasks that are blocking this task"""
        blocking = []
        if self.depends_on and not self.depends_on.completed:
            blocking.append(self.depends_on)
        return blocking
    
    def __repr__(self):
        return f'<Task {self.title}>'
