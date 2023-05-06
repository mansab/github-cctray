import os
import requests
import xml.etree.ElementTree as ET
from flask import Flask, request, make_response

app = Flask(__name__)


@app.route('/')
def index():
    owner = request.args.get("owner")
    repo = request.args.get("repo")
    token = os.environ.get("GITHUB_TOKEN")

    # GitHub API endpoint to retrieve workflow runs for a repository
    endpoint = "https://api.github.com/repos/{owner}/{repo}/actions/runs"

    # Check if the required parameters are present and not empty
    if not owner or not repo or not token:
        return make_response("Missing parameters", 400)

    # Build the API URL
    url = endpoint.format(owner=owner, repo=repo)

    # Add authentication to the request headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Send the API request
    response = requests.get(url, headers=headers)

    data = response.json()

    # Create root element for CCTray XML response
    root = ET.Element("Projects")

    # Loop through each workflow run and create a project element for each
    for run in data["workflow_runs"]:
        project = ET.SubElement(root, "Project")

        # Set project name
        project.set("name", repo)

        # Set last build status based on conclusion
        if run["conclusion"] == "success":
            project.set("lastBuildStatus", "Success")
        elif run["conclusion"] == "failure":
            project.set("lastBuildStatus", "Failure")
        else:
            project.set("lastBuildStatus", "Unknown")

        # Set last build time
        project.set("lastBuildTime", run["updated_at"])

        # Set web URL for project
        project.set("webUrl", run["html_url"])

    # Return CCTray XML response
    response = make_response(ET.tostring(root).decode())
    response.headers['Content-Type'] = 'application/xml'
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
