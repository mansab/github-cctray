# Github-CCTray

A lightweight App that provides [all Github Workflows of a Repository](https://docs.github.com/en/rest/actions/workflow-runs?apiVersion=2022-11-28#list-workflow-runs-for-a-repository) in [CCTray Specification](https://cctray.org/v1/).

![STATUS](https://github.com/mansab/github-cctray/actions/workflows/.github/workflows/pylint.yml/badge.svg)
![STATUS](https://github.com/mansab/github-cctray/actions/workflows/.github/workflows/unittests.yml/badge.svg)
![STATUS](https://github.com/mansab/github-cctray/actions/workflows/.github/workflows/codeql.yml/badge.svg)

# Usecase
Visibility for your Github Actions & Workflows in one place.

You can use the App to configure [CCTray Clients](https://cctray.org/clients/):
* [CCMenu](https://ccmenu.org/) `[tested]` ([more info](#configuring-a-client-ccmenu))
* [Nevergreen Dashboard](https://github.com/build-canaries/nevergreen) `[tested]`
# Running the App

## Prerequisites

### Authentication Token

To authenticate with Github API, the app needs a `token`, 
it can be provided by **either** of the following methods:

#### Github Personal Access Token
* [FGPAT (recommended) or PAT](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
* Read-Only access to Actions (Workflows, workflow runs and artifacts) required for Private repos.
* You will need to set: `GITHUB_TOKEN="<your_token>"` as the environment variable.

#### Github APP (Recommened)
* [Create a Github APP](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app) and grant Read-Only access to Github Actions
* The Github APP should be installed on the Github Organization or Account with access to the required repositories.
* You will need to set the following environment variable:
```
APP_AUTH_ID=<id_of_your_github_app>
APP_AUTH_PRIVATE_KEY=<private_key_of_your_github_app>
APP_AUTH_INSTALLATION_ID=<installtion_id_once_installed>
```
* Please refer to Github's offical documentation to know what these values are and where can you find them 

**Please take into account the [Github API rate limit](https://docs.github.com/en/rest/overview/resources-in-the-rest-api?apiVersion=2022-11-28#rate-limiting) for authentication tokens.**

## With Docker

### Build the Docker image

```bash
docker build -t github-cctray:latest . 
```

### Launch the Docker container

You can do this in two ways:

* Personal Access Token method

```bash
 docker run -p 8000:8000 \
            -e GITHUB_TOKEN="<your_token>" \
            -e BASIC_AUTH_USERNAME="<your_username>" \
            -e BASIC_AUTH_PASSWORD="<your_password>" \
            github-cctray:latest
```

* Github App method

```bash
 docker run -p 8000:8000 \
            -e APP_AUTH_ID="<id_of_your_github_app>" \
            -e APP_AUTH_PRIVATE_KEY="<private_key_of_your_github_app>" \
            -e APP_AUTH_INSTALLATION_ID="<installtion_id_once_installed>" \
            -e BASIC_AUTH_USERNAME="<your_username>" \
            -e BASIC_AUTH_PASSWORD="<your_password>" \
            github-cctray:latest
```

# Usage

Once up, the App binds to port `8000` by default and should be available at: http://localhost:8000

## Making an HTTP request

The App accepts GET requests with following parameters:

**manadatory parameters**

* `owner` - Organisation or User who owns the repository
* `repo` - Name of the Repository

**optional parameter**

* `token` - If you want to use FGPAT per user to access the API, to overcome Github API rate limiting (this takes precedence over the token/Github App auth set in the env var).

For Example:

* Mandatory Parameters
```bash
curl -X GET http://localhost:8000?owner=<repo_owner>&repo=<repository_name>
```

* Optional Parameter
```bash
curl -X GET http://localhost:8000?owner=<repo_owner>&repo=<repository_name&token=<your_token>
```

## Response

The above request would return an XML response (CCTray Specification) with all the workflows of a repository, while filtering them to return only **Unique & Latest** runs:

```bash
<Projects>
<Project name="github-cctray/CodeQL" activity="Sleeping" lastBuildStatus="Success" lastBuildTime="2023-05-07T23:22:02Z" webUrl="https://github.com/mansab/github-cctray/actions/runs/4909813101"/>
<Project name="github-cctray/Pylint" activity="Sleeping" lastBuildStatus="Success" lastBuildTime="2023-05-07T23:19:13Z" webUrl="https://github.com/mansab/github-cctray/actions/runs/4909813107"/>
<Project name="github-cctray/TestUnit" activity="Sleeping" lastBuildStatus="Success" lastBuildTime="2023-05-07T23:18:59Z" webUrl="https://github.com/mansab/github-cctray/actions/runs/4909813102"/>
</Projects>
```

Attributes are returned as follows:

<table>
  <thead>
    <tr>
      <th>Name</th>
      <th>Description</th>
      <th>Type</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>name</td>
      <td>Name of the repository and the workflow</td>
      <td>string : repo_name/workflow</td>
    </tr>
    <tr>
      <td>activity</td>
      <td>the current state of the project</td>
      <td>string enum : Sleeping, Building</td>
    </tr>
    <tr>
      <td>lastBuildStatus</td>
      <td>a brief description of the last build</td>
      <td>string enum : Success, Failure, Unknown</td>
    </tr>
    <tr>
      <td>lastBuildTime</td>
      <td>when the last build occurred</td>
      <td>DateTime</td>
    </tr>
    <tr>
      <td>webUrl</td>
      <td>Exact URL of the Github Action run for a workflow</td>
      <td>string (URL)</td>
    </tr>
  </tbody>
</table>

## Health check

The App has an health endpoint which returns the status and version of the app

```bash
curl -X GET http://localhost:8000/health
```


### Response

```
{"status":"ok","version":"2.2.0"}
```

## Rate Limiting

Github has Rate Limiting for their APIs, to check if you are rate limited, use this endpoint

* With token in the environment variable
```bash
curl -X GET http://localhost:8000/limit
```

* With token in the query parameter
```bash
curl -X GET http://localhost:8000/limit?token=<your_token>
```

### Response

```
{"rate_limit":{"limit":5000,"remaining":1724,"reset":1686920826,"reset_cest":"2023-06-16 15:07:06 UTC+02:00+0200","used":3276},"status":"ok"}
```

# Development Setup

* Python 3.9
* pip 
* Activate [Python virtualenv](https://python.land/virtual-environments/virtualenv)

```bash
python -m venv venv
source venv/bin/activate
```

* Install requirements

```bash
pip install -r requirements.txt
```

* Execute

```bash
* set necessary env variable to authenticate with Github (see Prerequisites)
* export BASIC_AUTH_USERNAME=<user>
* export BASIC_AUTH_PASSWORD=<pass>
* python app.py
```

# Configuring a Client 

## CCMenu

You can configure a CCTray client by adding above App's URL with parameters and select the required or all the workflows in your Github respository.

In the below snapshots you can see CCMenu configured against this project's repository workflows as an example:

### Desktop Menu Bar

<img src="./images/ccmenu_desktop_menu_bar.png?raw=true" />

### Project Configuration

<img src="./images/ccmenu_projects_configuration.png?raw=true" />

## Nevergreen

### Dashboard

<img src="./images/nevergreen_dashboard.png?raw=true" />

### Configuration

<img src="./images/nevergreen_dashboard_configuration.png?raw=true" />

