import unittest
from unittest.mock import patch
from src.routes import app

class RoutesTestCase(unittest.TestCase):

    def setUp(self):
        """Set up the test environment."""
        app.testing = True
        app.config['BASIC_AUTH_USERNAME'] = 'user'
        app.config['BASIC_AUTH_PASSWORD'] = 'pass'
        self.client = app.test_client()
        self.headers = {
            'Authorization': 'Basic dXNlcjpwYXNz'
        }

    @patch("src.routes.get_token")
    @patch("src.routes.get_all_workflow_runs")
    def test_index(self, mock_get_all_workflow_runs, mock_get_token):
        """Test case for the index route."""
        mock_get_token.return_value = "mocked_token"

        # Mock the response from get_all_workflow_runs
        mock_get_all_workflow_runs.return_value = [
            {
                "name": "workflow1",
                "status": "completed",
                "conclusion": "success",
                "updated_at": "2023-07-05T12:00:00Z",
                "html_url": "https://github.com/test_owner/test_repo/actions/runs/1",
                "head_commit": {"id": "1234567890abcdef"}
            },
            {
                "name": "workflow2",
                "status": "completed",
                "conclusion": "failure",
                "updated_at": "2023-07-04T12:00:00Z",
                "html_url": "https://github.com/test_owner/test_repo/actions/runs/2",
                "head_commit": {"id": "abcdef1234567890"}
            }
        ]

        response = self.client.get('/?owner=test_owner&repo=test_repo', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/xml')

        expected_xml = """<Projects>
        <Project name="test_repo/workflow1" activity="Sleeping" lastBuildStatus="Success" lastBuildTime="2023-07-05T12:00:00Z" webUrl="https://github.com/test_owner/test_repo/actions/runs/1" lastBuildLabel="12345678" />
        <Project name="test_repo/workflow2" activity="Sleeping" lastBuildStatus="Failure" lastBuildTime="2023-07-04T12:00:00Z" webUrl="https://github.com/test_owner/test_repo/actions/runs/2" lastBuildLabel="abcdef12" />
        </Projects>""".replace('\n', '').replace(' '*8, '')

        self.maxDiff = None  # Set self.maxDiff to None
        self.assertEqual(response.data.decode(), expected_xml)

        mock_get_token.assert_called_once()
        mock_get_all_workflow_runs.assert_called_once_with("test_owner", "test_repo", "mocked_token")


if __name__ == '__main__':
    unittest.main()
