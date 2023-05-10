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

* Github Personal Access Token
    * [FGPAT (recommended) or PAT](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
    * Read-Only access to Actions (Workflows, workflow runs and artifacts) required for Private repos.
* Development
    * Python 3.9
    * pip

## With Docker

* Build the Docker image

```bash
docker build -t github-cctray:latest . 
```

* Launch the Docker container

```bash
 docker run -p 8000:8000 -e GITHUB_TOKEN="<your_token>" github-cctray:latest
```

# Usage

Once up, the App binds to port `8000` by default and should be available at: http://localhost:8000

## Making an HTTP request

The App accepts GET and POST requests with **two manadatory parameters**:

* `owner` - Organisation or User who owns the repository
* `repo` - Name of the Repository

For Example:

* GET

```bash
curl -X GET http://localhost:8000?owner=<repo_owner>&repo=<repository_name>
```

* POST

```bash
curl -d "owner=<repo_owner>&repo=<repository_name>" -X POST http://localhost:8000
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

# Development Setup
 
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
export GITHUB_TOKEN=<token>
python app.py
```

# Configuring a Client 

## CCMenu

You can configure a CCTray client by adding above App's URL with parameters and select the required or all the workflows in your Github respository.

In the below snapshots you can see CCMenu configured against this project's repository workflows as an example:

## Desktop Menu Bar

<img src="./images/ccmenu_desktop_menu_bar.png?raw=true" />

## Project Configuration

<img src="./images/ccmenu_projects_configuration.png?raw=true" />
