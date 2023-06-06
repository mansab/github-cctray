"""Teat Module for the App"""
import unittest
from unittest.mock import patch
from app import app


class TestApp(unittest.TestCase):
    """Test cases for the App module."""

    def setUp(self):
        """Set up the test environment."""
        app.testing = True
        app.config['BASIC_AUTH_USERNAME'] = 'user'
        app.config['BASIC_AUTH_PASSWORD'] = 'pass'
        self.client = app.test_client()
        self.headers = {
            'Authorization': 'Basic dXNlcjpwYXNz'
        }

    def test_index_missing_parameters(self):
        """Test handling missing parameters in the index route."""
        response = self.client.get('/', headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Missing parameter(s)", response.data)

    @patch('app.get_all_workflow_runs')
    def test_index_successful_response(self, mock_get_all_workflow_runs):
        """Test successful response in the index route."""
        mock_get_all_workflow_runs.return_value = [
            {
                "name": "CI",
                "status": "completed",
                "conclusion": "success",
                "updated_at": "2021-09-20T18:25:34Z",
                "html_url": "https://github.com/owner/repo/actions/runs/1234"
            }
        ]
        response = self.client.get('/?owner=owner&repo=repo', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<Project', response.data)
        self.assertIn(b'name="repo/CI"', response.data)
        self.assertIn(b'activity="Sleeping', response.data)
        self.assertIn(b'lastBuildStatus="Success"', response.data)
        self.assertIn(b'webUrl="https://github.com/owner/repo/actions/runs/1234"', response.data)

    @patch('app.get_all_workflow_runs')
    def test_index_unknown_build_status(self, mock_get_all_workflow_runs):
        """Test unknown build status in the index route."""
        mock_get_all_workflow_runs.return_value = [
            {
                "name": "CI",
                "status": "in_progress",
                "conclusion": None,
                "updated_at": "2021-09-20T18:25:34Z",
                "html_url": "https://github.com/owner/repo/actions/runs/1234"
            }
        ]
        response = self.client.get('/?owner=owner&repo=repo', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<Project', response.data)
        self.assertIn(b'lastBuildStatus="Unknown"', response.data)

    @patch('app.get_all_workflow_runs')
    def test_index_failed_response(self, mock_get_all_workflow_runs):
        """Test failed response in the index route."""
        mock_get_all_workflow_runs.return_value = []
        response = self.client.get('/?owner=owner&repo=repo', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<Projects />', response.data)


if __name__ == '__main__':
    unittest.main()
