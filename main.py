import os
import argparse
import requests
import openai
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up environment variables
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# OpenAI configuration
openai.api_key = OPENAI_API_KEY

def get_merge_request_changes(project_id, merge_request_iid):
    url = f"https://gitlab.com/api/v4/projects/{project_id}/merge_requests/{merge_request_iid}/changes"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to get changes: {response.status_code}, {response.text}")

def format_changes(changes):
    formatted_changes = "\n".join([f"File: {change['new_path']}\nDiff:\n{change['diff']}" for change in changes['changes']])
    return formatted_changes

def get_code_review(formatted_changes, template):
    prompt = template.format(
        date=datetime.now().strftime("%Y-%m-%d"),
        merge_request_url="https://gitlab.com/your_project/merge_requests/your_merge_request_iid",
        code_changes=formatted_changes,
        review_comments="{review_comments}",
        suggestions="{suggestions}"
    )
    response = openai.Completion.create(
        engine="gpt-4",
        prompt=prompt,
        max_tokens=1500
    )
    return response.choices[0].text.strip()

def post_comment(project_id, merge_request_iid, comment):
    url = f"https://gitlab.com/api/v4/projects/{project_id}/merge_requests/{merge_request_iid}/notes"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    data = {"body": comment}
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 201:
        print("Comment posted successfully.")
    else:
        raise Exception(f"Failed to post comment: {response.status_code}, {response.text}")

def main():
    parser = argparse.ArgumentParser(description="AI Code Checker for GitLab CI/CD")
    parser.add_argument("--project_id", type=str, help="The ID of the GitLab project")
    parser.add_argument("--merge_request_iid", type=str, help="The IID of the merge request")

    args = parser.parse_args()

    project_id = args.project_id or os.getenv('CI_PROJECT_ID')
    merge_request_iid = args.merge_request_iid or os.getenv('CI_MERGE_REQUEST_IID')

    if not project_id or not merge_request_iid:
        raise ValueError("Project ID and Merge Request IID must be provided either as arguments or environment variables.")

    changes = get_merge_request_changes(project_id, merge_request_iid)
    formatted_changes = format_changes(changes)

    with open('review_template.md', 'r') as template_file:
        template = template_file.read()

    review = get_code_review(formatted_changes, template)
    post_comment(project_id, merge_request_iid, review)

if __name__ == "__main__":
    main()
