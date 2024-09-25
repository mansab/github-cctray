"""Helpers Module"""
import datetime
import time
import re
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
    GITHUB_APP_TOKEN,
)


def decode_base64(value):
    """Decodes a Base64 string

    Returns:
        value: Base64 Decoded value, utf-8 format.
    """
    return base64.b64decode(value).decode("utf-8")


def redact_token(uri):
    """Redacts the 'token' value from the URI

    Returns:
        uri: token=<REDACTED> 
    """
    return re.sub(r'(\?|&)token=.*?(&|$)', r'\1token=<REDACTED>\2', uri)


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

    if token is not None:
        return token
    elif args.mode == "pat-auth":
        token = GITHUB_TOKEN
    elif args.mode == "app-auth":
        token = GITHUB_APP_TOKEN
        if not token:
            print(f"\nObtain the Github App token by accessing: http://localhost:8000/auth")
            print(f"and set GITHUB_APP_TOKEN as environment variable.\n")
            raise Exception("Github APP token not found.")
    return token

def authenticate_with_device_flow():
    device_code_url = "https://github.com/login/device/code"
    client_id = APP_AUTH_ID
    payload = {
        "client_id": client_id,
        "scope": "repo",
    }

    headers = {
        "Accept": "application/json"
    }    

    response = requests.post(device_code_url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        device_code = data['device_code']
        user_code = data['user_code']
        verification_uri = data['verification_uri']
        print(f"\nActivate the app by accessing: {verification_uri}")
        print(f"and enter this activation code: {user_code}")

        token_url = "https://github.com/login/oauth/access_token"
        max_attempts = 2
        attempt = 0
        delay = 5

        while attempt < max_attempts:
            attempt += 1
            
            token_response = requests.post(token_url, json={
                "client_id": client_id,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
            }, headers={"Accept": "application/json"})

            if token_response.status_code == 200:
                token_data = token_response.json()
                return token_data.get("access_token")
            elif token_response.status_code == 400:
                error_data = token_response.json()
                if error_data.get("error") == "authorization_pending":
                    print(f"Authorization pending... Attempt {attempt}/{max_attempts}. Retrying in {delay} seconds.")
                    time.sleep(delay)
                else:
                    print(f"Error: {error_data.get('error_description')}")
                    return None
            else:
                print(f"Unexpected response: {token_response.status_code} {token_response.text}")
                return None

        print("Maximum attempts reached. Please try again.")
        return None
    else:
        raise Exception(f"Failed to initiate device flow: {response.status_code} {response.text}")



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
