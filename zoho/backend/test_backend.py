import unittest
import json
from app import create_app, db
from app.models import User, Holding

class BackendTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_add_coin(self):
        payload = {
            'command': 'addcoin',
            'user_id': 'user123',
            'channel_id': 'channel123',
            'args': 'bitcoin 0.5'
        }
        response = self.client.post('/api/cliq/event', json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Added 0.5 bitcoin', response.json['text'])
        
        # Verify DB
        with self.app.app_context():
            user = User.query.filter_by(cliq_user_id='user123').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.holdings.count(), 1)
            self.assertEqual(user.holdings[0].coin_id, 'bitcoin')
            self.assertEqual(user.holdings[0].amount, 0.5)

    def test_get_portfolio_cliq(self):
        # Add coin first
        self.test_add_coin()
        
        payload = {
            'command': 'portfolio',
            'user_id': 'user123',
            'channel_id': 'channel123'
        }
        response = self.client.post('/api/cliq/event', json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Your Portfolio', response.json['text'])
        self.assertIn('bitcoin', response.json['text'])

    def test_dashboard_endpoint(self):
        # Add coin first
        self.test_add_coin()
        
        response = self.client.get('/api/portfolio/user123')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data['holdings']), 1)
        self.assertEqual(data['holdings'][0]['coin'], 'bitcoin')

if __name__ == '__main__':
    unittest.main()
