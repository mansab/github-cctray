# Github-CCTray

A lightweight App that provides [Github Workflow Runs](https://docs.github.com/en/rest/actions/workflow-runs?apiVersion=2022-11-28#list-workflow-runs-for-a-repository) information in [CCTray Specification](https://cctray.org/v1/).

# Usecase

## CCMenu

You can use the App to configure [CCTray Clients](https://cctray.org/clients/) like [CCMenu](https://ccmenu.org/) `[tested]`.

# Running the App

## Prerequisites

* Python 3.9
* pip
* Github [PAT or FGPAT](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) with Workflow/Actions scope.

## Setup

* Activate [Python virtualenv](https://python.land/virtual-environments/virtualenv)

```bash
python -m venv venv
source venv/bin/activate
```

* Install requirements

```bash
pip install -r requirements.txt
```

## Execute

```bash
export GITHUB_TOKEN=<token>
python app.py
```

# Accessing the App

Once up, the App binds to port `8000` by default and should be available at: http://localhost:8000

## Making an HTTP request

The App accepts GET and POST requests with **two manadatory parameters** `owner` & `repo`.

For Example:

* GET

```bash
curl -X GET http://localhost:8000?owner<repo_owner>&repo<repository_name>
```

* POST

```bash
curl -d "owner=<repo_owner>&repo=<repository_name>" -X POST http://localhost:8000
```
