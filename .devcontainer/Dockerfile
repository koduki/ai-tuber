FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

# Install wget which is required by VSCode server install
RUN apt-get update && apt-get install -y wget

# Install dependencies for both services to allow development in one container
RUN pip install google-genai httpx sseclient-py google-adk fastapi uvicorn sse-starlette

# Set the default shell to bash rather than sh
ENV SHELL /bin/bash
