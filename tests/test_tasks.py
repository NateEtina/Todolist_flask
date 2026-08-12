import unittest
from app import create_app, db
from app.models import User, Task

class TaskTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        
        # Create test user and login
        self.user = User(username='testuser', email='test@test.com')
        self.user.set_password('password123')
        db.session.add(self.user)
        db.session.commit()
        
        self.client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def test_create_task(self):
        response = self.client.post('/task/new', data={
            'title': 'Test Task',
            'description': 'Test Description',
            'priority': 'high'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        task = Task.query.filter_by(title='Test Task').first()
        self.assertIsNotNone(task)
        self.assertEqual(task.priority, 'high')