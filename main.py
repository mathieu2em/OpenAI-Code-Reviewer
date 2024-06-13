import os
import argparse
import requests
import openai
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up environment variables
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Verify environment variables
if not GITLAB_TOKEN:
    raise ValueError("GITLAB_TOKEN not found in environment variables")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# OpenAI client initialization
client = openai.OpenAI(api_key=OPENAI_API_KEY)

MAX_TOKENS_PER_MINUTE = 40000
MAX_TOKENS_PER_REQUEST = 6000

def get_merge_request_changes(project_id, merge_request_iid):
    print("Fetching merge request changes...")
    url = f"https://git.thirdbridge.ca/api/v4/projects/{project_id}/merge_requests/{merge_request_iid}/changes"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print("Successfully fetched merge request changes.")
        return response.json()
    else:
        print(f"Failed to get changes: {response.status_code}, {response.text}")
        raise Exception(f"Failed to get changes: {response.status_code}, {response.text}")

def format_changes(changes):
    print("Formatting changes...")
    formatted_changes = "\n".join([f"File: {change['new_path']}\nDiff:\n{change['diff']}" for change in changes['changes']])
    print("Changes formatted.")
    return formatted_changes

def split_text(text, max_length):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 > max_length:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(word)
        current_length += len(word) + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def get_code_review(formatted_changes, template, project_id, merge_request_iid):
    print("Splitting changes into smaller chunks...")
    merge_request_url = f"https://git.thirdbridge.ca/{project_id}/merge_requests/{merge_request_iid}"
    chunks = split_text(formatted_changes, 5000)  # Adjust chunk size to fit within token limits
    total_chunks = len(chunks)
    print(f"Total chunks created: {total_chunks}")

    # Batch processing to respect the token per minute limit
    batches = []
    current_batch = []
    current_batch_length = 0

    for chunk in chunks:
        chunk_length = len(chunk.split())
        if current_batch_length + chunk_length + MAX_TOKENS_PER_REQUEST <= MAX_TOKENS_PER_MINUTE:
            current_batch.append(chunk)
            current_batch_length += chunk_length
        else:
            batches.append(current_batch)
            current_batch = [chunk]
            current_batch_length = chunk_length

    if current_batch:
        batches.append(current_batch)

    all_reviews = []
    total_tokens_used = 0

    for i, batch in enumerate(batches):
        print(f"Processing batch {i+1}/{len(batches)} with {len(batch)} chunks...")
        messages = [{"role": "system", "content": "You are an experienced programmer and you are asked to provide a clear and concise code review of the following changes."}]

        for chunk in batch:
            messages.append({"role": "user", "content": chunk})

        final_prompt = template.format(
            date=datetime.now().strftime("%Y-%m-%d"),
            merge_request_url=merge_request_url,
            review_comments="{review_comments}",
            suggestions="{suggestions}"
        )
        messages.append({"role": "user", "content": final_prompt})
        print("Sending batch to GPT-4...")

        response = client.chat.completions.create(
            messages=messages,
            model="gpt-4o",
        )

        review = response.choices[0].message.content.strip()
        print("Received response from GPT-4:")
        print(review)
        all_reviews.append(review)

        # Update total tokens used and check if a timeout is needed
        tokens_used = sum([len(msg['content'].split()) for msg in messages]) + 3000
        total_tokens_used += tokens_used
        print(f"Tokens used: {tokens_used}, Total tokens used: {total_tokens_used}")

        if total_tokens_used >= MAX_TOKENS_PER_MINUTE:
            print("Reached token limit, waiting for the next minute...")
            time.sleep(60)  # Wait for 1 minute before processing the next batch
            total_tokens_used = 0  # Reset the counter after the timeout

    return "\n\n".join(all_reviews)

def post_comment(project_id, merge_request_iid, comment):
    print("Posting comment to GitLab...")
    url = f"https://git.thirdbridge.ca/api/v4/projects/{project_id}/merge_requests/{merge_request_iid}/notes"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    data = {"body": comment}
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 201:
        print("Comment posted successfully.")
    else:
        print(f"Failed to post comment: {response.status_code}, {response.text}")
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

    # Debugging statements
    print(f"Project ID: {project_id}")
    print(f"Merge Request IID: {merge_request_iid}")
    print(f"GITLAB_TOKEN: {GITLAB_TOKEN[:4]}...")  # Only print first few characters for security

    changes = get_merge_request_changes(project_id, merge_request_iid)
    formatted_changes = format_changes(changes)

    with open('review_template.md', 'r') as template_file:
        template = template_file.read()

    review = get_code_review(formatted_changes, template, project_id, merge_request_iid)
    post_comment(project_id, merge_request_iid, review)

if __name__ == "__main__":
    main()
