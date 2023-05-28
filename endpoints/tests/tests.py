import json
import os
import unittest
from datetime import datetime, timedelta
from app import db
from app.models import Event
from app.api.utils import create_events_evolution_graph
from app import create_app, db

FILE_PATH = os.path.dirname(os.path.abspath(__file__))

class TestConfig(object):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    

class RestAPITests(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_average_pr_time(self):
        # Add sample events
        now = datetime.utcnow()
        event1 = Event(id='1', type='PullRequestEvent', repo_name='test_repo',
                       created_at=now)
        event2 = Event(id='2', type='PullRequestEvent', repo_name='test_repo',
                       created_at=now + timedelta(minutes=10))
        
        event3 = Event(id='3', type='PullRequestEvent', repo_name='test_repo',
                       created_at=now + timedelta(minutes=20))
        db.session.add(event1)
        db.session.add(event2)
        db.session.add(event3)
        db.session.commit()

        # Test the average pr time
        response =  self.client.get('http://localhost:5000/api/metrics/average_pr_time/test_repo')
        response_dict = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_dict, {"average_pr_time": 600})

    def test_empty_pr_time(self):
        # Test the average pr time
        response = self.client.get('/api/metrics/average_pr_time/test_repo')
        response_dict = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_dict, {"message": "Not enough data to compute average PR time", "info": "OK"})

    def test_event_counts(self):
        # Add sample events
        now = datetime.utcnow()
        events_in_time = [Event(id='1', type='PullRequestEvent', repo_name='test_repo', created_at=now),
                          Event(id='2', type='IssuesEvent', repo_name='test_repo', created_at=now)]
        events_out_of_time = [Event(id='3', type='PullRequestEvent', repo_name='test_repo', created_at=now - timedelta(minutes=10))]
        for event in events_in_time:
            db.session.add(event)
        for event in events_out_of_time:
            db.session.add(event)
        db.session.commit()

        # Test the event counts
        response = self.client.get('/api/metrics/event_counts/1')
        reponse_dict = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(reponse_dict, {"PullRequestEvent": 1, "IssuesEvent": 1, "WatchEvent": 0})

    def test_event_counts_per_minute(self):
        # We can't really test the api, because of the now and image but we can test the function
        dt = datetime(2020, 6, 14, 12, 0, 0)
        events = [Event(id='1', type='PullRequestEvent', repo_name='test_repo', created_at=dt),
                            Event(id='2', type='IssuesEvent', repo_name='test_repo', created_at=dt - timedelta(minutes=1))]
        img = create_events_evolution_graph(events, dt - timedelta(minutes=1), dt, ['PullRequestEvent', 'IssuesEvent', 'WatchEvent'])
        with open(os.path.join(FILE_PATH, 'resources', 'events_counts.jpg'), 'rb') as f:
            expected = f.read()
        self.assertEqual(img.getvalue(), expected)
        # save it to file
    

if __name__ == '__main__':
    unittest.main()
