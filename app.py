"""App Module"""
import os
import xml.etree.ElementTree as ET
import logging
from concurrent.futures import ThreadPoolExecutor
import requests as requests
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
    results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        page = 1
        while True:
            future = executor.submit(requests.get, f"{endpoint}?per_page=100&page={page}", headers=headers, timeout=10)
            futures.append(future)
            if 'next' in future.result().links and page <= 3:
                logger.info("Found next page %s, fetching more results...", page)
                page += 1
            else:
                break
        for future in futures:
            response = future.result()
            if response is None:
                logger.error("Failed to get response from GitHub API")
            elif response.status_code != 200:
                logger.error("GitHub API returned status code %d", response.status_code)
            else:
                data = response.json()
                results += data["workflow_runs"]

    return results


@app.route('/')
def index():
    owner = request.args.get("owner") or request.form.get('owner')
    repo = request.args.get("repo") or request.form.get('repo')
    token = os.environ.get("GITHUB_TOKEN")

    if not owner or not repo or not token:
        logger.warning("Missing parameter(s) or Environment Variable")
        return make_response("Missing parameter(s)", 400)

    data = get_workflow_runs(owner, repo, token)

    # Sort workflow runs by 'updated_at' timestamp in descending order
    workflow_runs = sorted(data, key=lambda run: run["updated_at"], reverse=True)

    root = ET.Element("Projects")
    project_names = set()  # Set to store unique project names

    for run in workflow_runs:
        project_name = repo + "/" + run["name"]
        if project_name not in project_names:  # Check if project name is already in the set
            project_names.add(project_name)  # Add project name to the set
            project = ET.SubElement(root, "Project")
            project.set("name", project_name)

            # Map 'status' field to 'activity'
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

    # Log request URI and response code
    logger.info("Request URI: %s Response Code: %d", request.path, response.status_code)


    return response


@app.errorhandler(Exception)
def handle_error(exception):
    # Log the error
    logger.error("An error occurred: %s", str(exception))

    return "An error occurred.", 500


if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8000)
