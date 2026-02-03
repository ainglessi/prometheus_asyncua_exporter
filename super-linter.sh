#!/bin/bash

# Get the current directory
REPO_DIR=$(pwd)
echo "$REPO_DIR"

docker pull ghcr.io/super-linter/super-linter:latest

# Run the Docker container with the specified environment variables and volume mount
docker run \
	-e FILTER_REGEX_EXCLUDE="deps/*" \
	-e IGNORE_GITIGNORED_FILES=true \
	-e LOG_LEVEL=INFO \
	-e DEFAULT_BRANCH=origin/main \
	-e RUN_LOCAL=true \
	-e VALIDATE_ALL_CODEBASE=false \
	-e VALIDATE_PYTHON_RUFF=true \
	-e VALIDATE_PYTHON_RUFF_FORMAT=true \
  -e VALIDATE_YAML_PRETTIER=true \
  -e VALIDATE_DOCKERFILE_HADOLINT=true \
  -e VALIDATE_MARKDOWN=true \
  -e FIX_PYTHON_RUFF=true \
  -e FIX_PYTHON_RUFF_FORMAT=true \
  -e FIX_MARKDOWN=true \
  -e FIX_YAML_PRETTIER=true \
	-v "$REPO_DIR:/tmp/lint" -it --rm ghcr.io/super-linter/super-linter:latest
