# This app requires a GitHub API token to access the GitHub Actions API.
# To set the token, run the container with the -e flag and specify the token
# as the value of the GITHUB_TOKEN environment variable.
# Example: docker run -p 8000:8000 -e GITHUB_TOKEN="<token>" github-cctray:latest
FROM python:3.9-slim-buster AS build

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.9-slim-buster AS app

RUN groupadd -r app && useradd --no-log-init -r -g app app

WORKDIR /app

COPY --from=build /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY app.py ./
COPY CHANGELOG.md ./

RUN chown -R app:app /app

USER app

EXPOSE 8000

ENTRYPOINT ["python", "app.py"]