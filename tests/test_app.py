"""Teat Module for the App"""
import unittest
from unittest.mock import patch, MagicMock
from app import get_workflows, get_workflow_runs, app, get_all_workflow_runs


class AppTests(unittest.TestCase):
    """Test cases for the App module."""

    def setUp(self):
        """Setup the app"""
        self.app = app.test_client()

    def test_get_workflows(self):
        """Test case for getting workflows"""
        owner = "test_owner"
        repo = "test_repo"
        headers = {"Authorization": "Bearer test_token",
                   "Accept": "application/vnd.github.v3+json"}

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "workflows": ["workflow1", "workflow2"]}
            mock_get.return_value = mock_response

            workflows = get_workflows(owner, repo, headers)

            self.assertEqual(workflows, ["workflow1", "workflow2"])

    def test_get_workflow_runs(self):
        """Test case for getting workflow runs"""
        workflow = {"url": "test_url"}
        headers = {"Authorization": "Bearer test_token",
                   "Accept": "application/vnd.github.v3+json"}

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "workflow_runs": ["run1", "run2"]}
            mock_get.return_value = mock_response

            workflow_runs = get_workflow_runs(workflow, headers)

            self.assertEqual(workflow_runs, ["run1", "run2"])

    def test_get_all_workflow_runs(self):
        """Test case for getting all workflow runs"""
        owner = "test_owner"
        repo = "test_repo"
        token = "test_token"
        headers = {"Authorization": "Bearer test_token",
                   "Accept": "application/vnd.github.v3+json"}
        workflows = [{"url": "workflow1"}, {"url": "workflow2"}]
        runs1 = [{"id": 1, "status": "completed", "conclusion": "success"}]
        runs2 = [{"id": 2, "status": "completed", "conclusion": "failure"}]

        with patch('app.get_workflows') as mock_get_workflows, \
                patch('app.get_workflow_runs') as mock_get_workflow_runs:

            mock_get_workflows.return_value = workflows
            mock_get_workflow_runs.side_effect = [runs1, runs2]

            result = get_all_workflow_runs(owner, repo, token)

            self.assertEqual(result, runs1 + runs2)
            mock_get_workflows.assert_called_once_with(owner, repo, headers)
            mock_get_workflow_runs.assert_any_call(workflows[0], headers)
            mock_get_workflow_runs.assert_any_call(workflows[1], headers)
