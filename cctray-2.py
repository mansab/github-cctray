import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

owner = os.environ.get("GITHUB_USERNAME")
repo = os.environ.get("GITHUB_REPOSITORY")
token = os.environ.get("GITHUB_TOKEN")

# GitHub API endpoint to retrieve workflow runs for a repository
endpoint = "https://api.github.com/repos/{owner}/{repo}/actions/runs"

# Build the API URL
url = endpoint.format(owner=owner, repo=repo)

# Add authentication to the request headers
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json"
}

# Send the API request
response = requests.get(url, headers=headers)

# Parse the response JSON
runs = response.json()["workflow_runs"]

# Build the CCTray-compatible XML response
root = ET.Element("Projects")

for run in runs:
    project = ET.SubElement(root, "Project")
    project.set("name", run["name"])
    project.set("lastBuildStatus", "Unknown")
    project.set("lastBuildLabel", run["head_branch"])
    project.set("activity", "Building" if run["status"] == "in_progress" else "Sleeping")
    project.set("webUrl", run["html_url"])
    project.set("lastBuildTime", datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%dT%H:%M:%S.%fZ"))

# Output the XML response
xmlstr = ET.tostring(root, encoding="unicode")
print(xmlstr)

