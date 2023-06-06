"""App Module"""
import os
import logging
from concurrent.futures import ThreadPoolExecutor

import xml.etree.ElementTree as ET
import requests
from flask import Flask, request, make_response
from flask_basicauth import BasicAuth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask('github-cctray')
app.config['BASIC_AUTH_USERNAME'] = os.environ.get("BASIC_AUTH_USERNAME")
app.config['BASIC_AUTH_PASSWORD'] = os.environ.get("BASIC_AUTH_PASSWORD")

basic_auth = BasicAuth(app)

API_BASE_URL = "https://api.github.com"
MAX_WORKERS = 10
TIMEOUT = 10


def get_workflows(owner, repo, headers):
    """Get the workflows for a given owner and repo from the GitHub API.

    Args:
        owner (str): The owner of the repository.
        repo (str): The repository name.
        headers (dict): HTTP headers to be sent with the request.

    Returns:
        list: A list of workflows for the given repository.

    Raises:
        requests.HTTPError: If the request to the GitHub API fails.
    """
    endpoint = f"{API_BASE_URL}/repos/{owner}/{repo}/actions/workflows"
    response = requests.get(endpoint, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()["workflows"]


def get_workflow_runs(workflow, headers):
    """Get the workflow runs for a specific workflow from the GitHub API.

    Args:
        workflow (dict): The workflow information.
        headers (dict): HTTP headers to be sent with the request.

    Returns:
        list: A list of workflow runs for the given workflow.

    Raises:
        requests.HTTPError: If the request to the GitHub API fails.
    """
    url = f"{workflow['url']}/runs"
    response = requests.get(url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()["workflow_runs"]


def get_all_workflow_runs(owner, repo, token):
    """Get all workflow runs for a given owner, repo, and token.

    Args:
        owner (str): The owner of the repository.
        repo (str): The repository name.
        token (str): The GitHub token for authentication.

    Returns:
        list: A list of all workflow runs for the given repository.

    Raises:
        requests.HTTPError: If the request to the GitHub API fails.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    workflows = get_workflows(owner, repo, headers)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(get_workflow_runs, workflow, headers) for workflow in workflows]

    results = []
    for future in futures:
        data = future.result()
        results += data

    return results


@app.route('/')
@basic_auth.required
def index():
    """Endpoint for generating the CCTray XML.

    Returns:
        flask.Response: The XML response containing the project information.
    """

    owner = request.args.get("owner") or request.form.get('owner')
    repo = request.args.get("repo") or request.form.get('repo')
    token = os.environ.get("GITHUB_TOKEN")

    if not owner or not repo or not token:
        logger.warning("Missing parameter(s) or Environment Variable")
        return make_response("Missing parameter(s)", 400)

    data = get_all_workflow_runs(owner, repo, token)

    workflow_runs = sorted(data, key=lambda run: run["updated_at"], reverse=True)

    root = ET.Element("Projects")
    project_names = set()  # Set to store unique project names

    for run in workflow_runs:
        project_name = repo + "/" + run["name"]
        if project_name not in project_names:  # Check if project name is already in the set
            project_names.add(project_name)  # Add project name to the set
            project = ET.SubElement(root, "Project")
            project.set("name", project_name)

            # Map 'Github' attributes to 'CCTray'
            if run["status"] == "completed":
                if run["conclusion"] == "success":
                    project.set("activity", "Sleeping")
                elif run["conclusion"] == "failure":
                    project.set("activity", "Sleeping")
            else:
                project.set("activity", "Building")

            project.set("lastBuildStatus", "Success"
                        if run["conclusion"] == "success"
                        else "Failure"
                        if run["conclusion"] == "failure"
                        else "Unknown")
            project.set("lastBuildTime", run["updated_at"])
            project.set("webUrl", run["html_url"])

    response = make_response(ET.tostring(root).decode())
    response.headers['Content-Type'] = 'application/xml'

    logger.info("Request URI: %s Response Code: %d", request.path, response.status_code)


    return response


@app.errorhandler(Exception)
def handle_error(exception):
    """Error handler for handling exceptions raised in the application.

    Args:
        exception (Exception): The exception object.

    Returns:
        str: The error message response.
    """
    logger.error("An error occurred: %s", str(exception))
    return "An error occurred.", 500


if __name__ == '__main__':
    from waitress import serve

    serve(app, host='0.0.0.0', port=8000)
