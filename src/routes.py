"""Routes Module"""
import re
import logging
import xml.etree.ElementTree as ET
import datetime
import requests
from flask import Flask, request, make_response, jsonify
from flask_basicauth import BasicAuth
from helpers import get_token, get_all_workflow_runs
from config import BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD, TIMEOUT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask('github-cctray')
app.config['BASIC_AUTH_USERNAME'] = BASIC_AUTH_USERNAME
app.config['BASIC_AUTH_PASSWORD'] = BASIC_AUTH_PASSWORD

basic_auth = BasicAuth(app)

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
    with open('../CHANGELOG.md', 'r', encoding='utf-8') as changelog_file:
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
