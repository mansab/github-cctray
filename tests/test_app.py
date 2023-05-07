import unittest
from unittest.mock import patch
from app import app


class TestApp(unittest.TestCase):

    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    def test_index_missing_parameters(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Missing parameter(s)", response.data)

    @patch('app.get_workflow_runs')
    def test_index_successful_response(self, mock_workflow_runs):
        mock_workflow_runs.return_value = {
            "workflow_runs": [
                {
                    "name": "CI",
                    "conclusion": "success",
                    "updated_at": "2021-09-20T18:25:34Z",
                    "html_url": "https://github.com/owner/repo/actions/runs/1234"
                }
            ]
        }
        response = self.client.get('/?owner=owner&repo=repo')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<Project', response.data)
        self.assertIn(b'name="repo/CI"', response.data)
        self.assertIn(b'lastBuildStatus="Success"', response.data)
        self.assertIn(b'webUrl="https://github.com/owner/repo/actions/runs/1234"', response.data)

    @patch('app.get_workflow_runs')
    def test_index_unknown_build_status(self, mock_workflow_runs):
        mock_workflow_runs.return_value = {
            "workflow_runs": [
                {
                    "name": "CI",
                    "conclusion": None,
                    "updated_at": "2021-09-20T18:25:34Z",
                    "html_url": "https://github.com/owner/repo/actions/runs/1234"
                }
            ]
        }
        response = self.client.get('/?owner=owner&repo=repo')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<Project', response.data)
        self.assertIn(b'lastBuildStatus="Unknown"', response.data)

    @patch('app.get_workflow_runs')
    def test_index_failed_response(self, mock_workflow_runs):
        mock_workflow_runs.return_value = None
        response = self.client.get('/?owner=owner&repo=repo')
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"An error occurred.", response.data)


if __name__ == '__main__':
    unittest.main()
