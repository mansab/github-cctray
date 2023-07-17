"""Helpers Module"""
import datetime
import base64
import argparse
from concurrent.futures import ThreadPoolExecutor
import jwt
import requests
from flask import request
from config import (
    API_BASE_URL,
    MAX_WORKERS,
    TIMEOUT,
    GITHUB_TOKEN,
    APP_AUTH_ID,
    APP_AUTH_BASE_URL,
    APP_AUTH_INSTALLATION_ID,
    B64_APP_AUTH_PRIVATE_KEY,
)


def decode_base64(value):
    return base64.b64decode(value).decode("utf-8")


def get_token():
    """Sets the GitHub API token based on the selected mode

    Returns:
        token: Either the personal access token or the GitHub App access token
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["pat-auth", "app-auth"],
        default="pat-auth",
        help="Authentication mode",
    )
    args = parser.parse_args()

    token = request.args.get("token")

    if token:
        return token
    elif args.mode == "pat-auth":
        token = GITHUB_TOKEN
    elif args.mode == "app-auth":
        app_auth_id = APP_AUTH_ID
        B64_APP_AUTH_PRIVATE_KEY = decode_base64(B64_APP_AUTH_PRIVATE_KEY)
        app_auth_installation_id = APP_AUTH_INSTALLATION_ID
        app_auth_base_url = APP_AUTH_BASE_URL

        now = datetime.datetime.utcnow()
        iat = int((now - datetime.datetime(1970, 1, 1)).total_seconds())
        exp = iat + 600
        payload = {"iat": iat, "exp": exp, "iss": app_auth_id}
        encoded_jwt = jwt.encode(payload, B64_APP_AUTH_PRIVATE_KEY, algorithm="RS256")
        headers = {
            "Authorization": f"Bearer {encoded_jwt}",
            "Accept": "application/vnd.github.v3+json",
        }
        response = requests.post(
            f"{app_auth_base_url}/app/installations/{app_auth_installation_id}/access_tokens",
            headers=headers,
            timeout=TIMEOUT,
        )

        if response.status_code == 201:
            token = response.json()["token"]
        else:
            raise Exception(
                f"Failed to obtain access token: {response.status_code} {response.text}"
            )

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
        "Accept": "application/vnd.github.v3+json",
    }

    workflows = get_workflows(owner, repo, headers)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(get_workflow_runs, workflow, headers)
            for workflow in workflows
        ]

    results = []
    for future in futures:
        data = future.result()
        results += data

    return results
