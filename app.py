"""App Module"""
import os
import re
import logging
import argparse
import datetime
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

import jwt
import requests
from flask import Flask, request, make_response, jsonify
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

def get_token():
    """Sets the GitHub API token based on the selected mode

    Returns:
        token: Either the personal access token or the GitHub App access token
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=[
            "pat-auth",
            "app-auth"],
        default="pat-auth",
        help="Authentication mode")
    args = parser.parse_args()

    token = request.args.get("token")

    if token:
        return token
    elif args.mode == "pat-auth":
        token = os.environ.get("GITHUB_TOKEN")
    elif args.mode == "app-auth":
        app_auth_id = os.environ.get("APP_AUTH_ID")
        app_auth_private_key = os.environ.get("APP_AUTH_PRIVATE_KEY")
        app_auth_installation_id = os.environ.get("APP_AUTH_INSTALLATION_ID")
        app_auth_base_url = "https://api.github.com"

        now = datetime.datetime.utcnow()
        iat = int((now - datetime.datetime(1970, 1, 1)).total_seconds())
        exp = iat + 600
        payload = {
            "iat": iat,
            "exp": exp,
            "iss": app_auth_id
        }
        encoded_jwt = jwt.encode(
            payload,
            app_auth_private_key,
            algorithm="RS256")
        headers = {
            "Authorization": f"Bearer {encoded_jwt}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.post(
            f"{app_auth_base_url}/app/installations/{app_auth_installation_id}/access_tokens",
            headers=headers,
            timeout=TIMEOUT)

        if response.status_code == 201:
            token = response.json()["token"]
        else:
            raise Exception(
                f"Failed to obtain access token: {response.status_code} {response.text}")

    return token


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
        futures = [
            executor.submit(
                get_workflow_runs,
                workflow,
                headers) for workflow in workflows]

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
    token = get_token()

    if not owner or not repo or not token:
        logger.warning("Missing parameter(s) or Environment Variable")
        return make_response("Missing parameter(s)", 400)

    data = get_all_workflow_runs(owner, repo, token)

    workflow_runs = sorted(
        data,
        key=lambda run: run["updated_at"],
        reverse=True)

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
            short_commit_id = run["head_commit"]["id"][:8]
            project.set("lastBuildLabel", short_commit_id)

    response = make_response(ET.tostring(root).decode())
    response.headers['Content-Type'] = 'application/xml'

    logger.info("Request URI: %s Response Code: %d",
                request.path, response.status_code)

    return response


@app.route('/health')
def health():
    """Endpoint for checking the health status.

    Returns:
        flask.Response: JSON response containing the status and version.
    """
    with open('CHANGELOG.md', 'r', encoding='utf-8') as changelog_file:
        changelog_content = changelog_file.read()

    latest_version_match = re.search(
        r'##\s*(\d+\.\d+\.\d+)', changelog_content)
    latest_version = latest_version_match.group(
        1) if latest_version_match else 'Unknown'

    response = {
        'status': 'ok',
        'version': f'{latest_version}'
    }

    return jsonify(response)


@app.route('/limit')
@basic_auth.required
def limit():
    """Endpoint for checking the rate limit status.

    Returns:
        flask.Response: JSON response containing rate limiting information.
    """
    token = get_token()
    headers = {
        'Accept': 'application/vnd.github+json',
        "Authorization": f"Bearer {token}",
        'X-GitHub-Api-Version': '2022-11-28'
    }
    url = 'https://api.github.com/rate_limit'
    response = requests.get(url, headers=headers, timeout=TIMEOUT)

    if response.status_code == 200:
        rate = response.json().get('rate', {})
        reset_unix_time = rate.get('reset', 0)
        reset_datetime = datetime.datetime.fromtimestamp(reset_unix_time)
        reset_cest = reset_datetime.astimezone(
            datetime.timezone(datetime.timedelta(hours=2)))
        rate['reset_cest'] = reset_cest.strftime('%Y-%m-%d %H:%M:%S %Z%z')

        if rate.get('remaining', 0) == 0:
            response = {
                'status': 'rate_limited',
                'rate_limit': rate
            }
        else:
            response = {
                'status': 'ok',
                'rate_limit': rate
            }
    else:
        response = {'status': 'ok', 'rate_limit': {
            'error': 'Failed to retrieve rate limit information'}}

    return jsonify(response)


@app.errorhandler(Exception)
def handle_error(exception):
    """Error handler for handling exceptions raised in the application.

    Args:
        exception (Exception): The exception object.

    Returns:
        str: The error message response.
    """
    logger.error("An error occurred: %s", str(exception))
    error_message = f"An error occurred: {str(exception)}"
    return error_message, 500


if __name__ == '__main__':
    from waitress import serve

    serve(app, host='0.0.0.0', port=8000)
