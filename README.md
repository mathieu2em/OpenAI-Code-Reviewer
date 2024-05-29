# AI Code Checker for GitLab CI/CD

This repository hosts a project that integrates an AI code reviewer into GitLab's CI/CD pipeline. The AI code checker utilizes the OpenAI API to review code changes in merge requests and post comments directly on the merge request.

## Table of Contents

- [AI Code Checker for GitLab CI/CD](#ai-code-checker-for-gitlab-cicd)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Setup](#setup)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
  - [Usage](#usage)
  - [Configuration](#configuration)
    - [Review Template](#review-template)
    - [Script Arguments](#script-arguments)
  - [Contributing](#contributing)
  - [License](#license)

## Features

- Automatically extracts code changes from GitLab merge requests.
- Queries OpenAI API for code review based on team and project-specific style guides.
- Posts AI-generated code review comments directly on the merge request.

## Setup

### Prerequisites

- GitLab account with access to your repository.
- OpenAI account with API access.
- Python 3.6+ installed on your local machine or CI environment.
- Required Python packages (listed in `requirements.txt`).

### Installation

1. **Clone the repository**:
    ```bash
    git clone https://gitlab.com/your_username/ai-code-checker.git
    cd ai-code-checker
    ```

2. **Create a virtual environment and install dependencies**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3. **Configure environment variables**:
    Create a `.env` file in the root directory with the following variables:
    ```bash
    GITLAB_TOKEN=your_gitlab_access_token
    OPENAI_API_KEY=your_openai_api_key
    ```

## Usage

1. **Extract code changes and generate review**:
    Run the script to fetch code changes from a specific merge request and generate a review. You can either set the project ID and merge request IID as environment variables or pass them as arguments to the script.

    **Using environment variables**:
    ```bash
    export CI_PROJECT_ID=your_project_id
    export CI_MERGE_REQUEST_IID=your_merge_request_iid
    python main.py
    ```

    **Using command-line arguments**:
    ```bash
    python main.py --project_id YOUR_PROJECT_ID --merge_request_iid YOUR_MERGE_REQUEST_IID
    ```

2. **Automate with GitLab CI/CD**:
    Integrate the script into your GitLab CI/CD pipeline by adding the following to your `.gitlab-ci.yml`:
    ```yaml
    stages:
      - review

    review_code:
      stage: review
      script:
        - source venv/bin/activate
        - python main.py --project_id $CI_PROJECT_ID --merge_request_iid $CI_MERGE_REQUEST_IID
      only:
        - merge_requests
    ```

## Configuration

### Review Template

The AI review template can be customized in the `review_template.md` file. This template includes placeholders for the date, merge request URL, code changes, review comments, and suggestions for improvement.

### Script Arguments

- `--project_id`: The ID of the GitLab project.
- `--merge_request_iid`: The IID of the merge request.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes. Make sure to follow the project's coding style and include tests for any new features or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.