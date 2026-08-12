import unittest
from flask import url_for
from app import create_app, db
from app.models import User

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def test_registration(self):
        response = self.client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'test@test.com',
            'password': 'password123',
            'password2': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(user)
        
    def test_login(self):
        user = User(username='testuser', email='test@test.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        response = self.client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)