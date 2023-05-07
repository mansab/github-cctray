import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from app import app


class TestGithubCCTray(unittest.TestCase):

    @patch('app.req.get')
    def test_index_returns_valid_xml_response(self, mock_get):
        # Arrange
        mock_get.return_value.json.return_value = {
            "workflow_runs": [
                {
                    "conclusion": "success",
                    "updated_at": "2022-01-01T00:00:00Z",
                    "html_url": "https://github.com/owner/repo/actions/runs/123"
                }
            ]
        }

        # Act
        response = app.test_client().get('/?owner=owner&repo=repo')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/xml')

        root = ET.fromstring(response.data)

        self.assertEqual(len(root.findall('Project')), 1)
        project = root.find('Project')
        self.assertEqual(project.attrib['name'], 'repo')
        self.assertEqual(project.attrib['lastBuildStatus'], 'Success')
        self.assertEqual(project.attrib['lastBuildTime'], '2022-01-01T00:00:00Z')
        self.assertEqual(project.attrib['webUrl'], 'https://github.com/owner/repo/actions/runs/123')

    def test_index_missing_parameters(self):
        # Arrange
        expected_response = b'Missing parameters'

        # Act
        response = app.test_client().get('/')

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, expected_response)

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'token'})
    @patch('app.req.get')
    def test_get_workflow_runs_called_with_correct_params(self, mock_get):
        # Arrange
        owner = 'owner'
        repo = 'repo'
        token = 'token'
        expected_endpoint = f'https://api.github.com/repos/{owner}/{repo}/actions/runs'
        expected_headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        # Act
        app.test_client().get(f'/?owner={owner}&repo={repo}')

        # Assert
        mock_get.assert_called_with(expected_endpoint, headers=expected_headers)
