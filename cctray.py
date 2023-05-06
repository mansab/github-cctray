import os
import requests
import xml.etree.ElementTree as ET

# Get the GitHub repository information from environment variables
username = os.environ.get("GITHUB_USERNAME")
repository = os.environ.get("GITHUB_REPOSITORY")
token = os.environ.get("GITHUB_TOKEN")

# Check if the environment variables are set and not empty
if not username or not repository or not token:
    raise ValueError("Required environment variables are missing or empty")

# Set the URL of the GitHub Workflow API for the repository
url = f"https://api.github.com/repos/{username}/{repository}/actions/workflows"

# Set the authorization headers for the API request
headers = {"Authorization": f"token {token}"}

# Make a request to the API to get information about the workflows
response = requests.get(url, headers=headers)

# Parse the response as JSON
data = response.json()

# Create the root element of the XML tree
root = ET.Element("Projects")

# Loop through each workflow in the response
for workflow in data["workflows"]:
    # Create a new project element for this workflow
    project = ET.SubElement(root, "Project")

    # Set the name of the project to the name of the workflow
    project.set("name", workflow["name"])

    # Set the activity of the project based on the status of the latest run
    if "runs" in workflow and len(workflow["runs"]) > 0:
        latest_run = workflow["runs"][0]
        if latest_run["status"] == "completed":
            if latest_run["conclusion"] == "success":
                project.set("activity", "Sleeping")
            else:
                project.set("activity", "Building")
        else:
            project.set("activity", "Building")
    else:
        project.set("activity", "Sleeping")

    # Set the last build status of the project based on the status of the latest run
    if "runs" in workflow and len(workflow["runs"]) > 0:
        latest_run = workflow["runs"][0]
        if latest_run["status"] == "completed":
            if latest_run["conclusion"] == "success":
                project.set("lastBuildStatus", "Success")
            else:
                project.set("lastBuildStatus", "Failure")
        else:
            project.set("lastBuildStatus", "Unknown")
    else:
        project.set("lastBuildStatus", "Unknown")

    # Set the URL of the project to the URL of the workflow on GitHub
    project.set("webUrl", workflow["html_url"])

    # Set the last build time of the project to the timestamp of the latest run
    if "runs" in workflow and len(workflow["runs"]) > 0:
        latest_run = workflow["runs"][0]
        project.set("lastBuildTime", latest_run["updated_at"])
    else:
        project.set("lastBuildTime", "")

# Generate the XML string from the XML tree
xml_string = ET.tostring(root, encoding="unicode")

# Return the XML string
print(xml_string)

