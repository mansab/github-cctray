"""App Module"""
import os
import xml.etree.ElementTree as ET
import logging
import requests as req
from flask import Flask, request, make_response

app = Flask('github-cctray')

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = app.logger


def get_workflow_runs(owner, repo, token):
    endpoint = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = req.get(endpoint, headers=headers)
    return response.json()


@app.route('/')
def index():
    owner = request.args.get("owner") or request.form.get('owner')
    repo = request.args.get("repo") or request.form.get('repo')
    token = os.environ.get("GITHUB_TOKEN")

    if not owner or not repo or not token:
        logger.warning("Missing parameters")
        return make_response("Missing parameters", 400)

    data = get_workflow_runs(owner, repo, token)

    root = ET.Element("Projects")

    for run in data["workflow_runs"]:
        project = ET.SubElement(root, "Project")

        project.set("name", repo)

        if run["conclusion"] == "success":
            project.set("lastBuildStatus", "Success")
        elif run["conclusion"] == "failure":
            project.set("lastBuildStatus", "Failure")
        else:
            project.set("lastBuildStatus", "Unknown")

        project.set("lastBuildTime", run["updated_at"])

        project.set("webUrl", run["html_url"])

    response = make_response(ET.tostring(root).decode())
    response.headers['Content-Type'] = 'application/xml'

    # Log request URI and response code
    logger.info(f"Request URI: {request.path} Response Code: {response.status_code}")

    return response


@app.errorhandler(Exception)
def handle_error(e):
    # Log the error
    logger.error(f"An error occurred: {str(e)}")
    return "An error occurred.", 500


if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8000)
