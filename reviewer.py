import os
import boto3
from github import Github
import json

# AWS 및 GitHub 설정
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_REGION = 'us-east-1'  # 사용할 AWS 리전
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# GitHub 클라이언트 초기화
g = Github(GITHUB_TOKEN)

# Bedrock 클라이언트 초기화
bedrock_client = boto3.client(
    'bedrock-runtime',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

def get_pr_diff(repo_name, pr_number):
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    # diff 텍스트를 저장할 리스트
    diff_text = []
    
    # PR에서 수정된 파일들 가져오기
    files = pr.get_files()
    for file in files:
        diff_text.append(f"File: {file.filename}\n{file.patch}\n")
    
    # 리스트를 문자열로 합치기
    return "\n".join(diff_text)

def generate_review(diff_text):
    prompt = (
                "Please answer in Korean.\n"
                "You are a strict and perfect code reviewer. You cannot tell any lies.\n"
                # "This is my development environment : springboot3, mybatis, postgresql.\n"
                "Below is the code patch, please help me do a detailed code review based on the following rules. Positive reviews are not needed:\n"
                "1. Pre-condition check: Verify if the function or method checks the state or range of values of variables necessary for it to work correctly.\n"
                "2. Runtime error check: Examine the code for potential runtime errors and identify other potential risks.\n"
                "3. Optimization: Inspect the code for optimization points. If the performance is suboptimal, recommend optimized code.\n"
                "4. Security issue: Check if the code uses modules with serious security flaws or contains security vulnerabilities.\n"
                # "- Provide the response in the following JSON format: {'reviews': [{'lineNumber': <line_number>, 'reviewComment': '<review comment>'}]}\n"
                # "- Provide comments and suggestions ONLY if there is something to improve, otherwise 'reviews' should be an empty array.\n"
                "- Write the comment in GitHub Markdown format.\n"
                "Please present the review comment in the following format.\n"
                "** Pre-condition check\n"
                "review contents\n"
                "** Runtime error check\n"
                "review contents\n"
                "** Optimization\n"
                "review contents\n"
                "** Security issue \n"
                "review contents\n"
                "If there is no review content for each item (pre-condition, runtime error, optimization, security issue), exclude the item from the results.\n"
                "- IMPORTANT: NEVER suggest adding comments to the code.\n\n"
                # f"Review the following code diff in the file '{file_path}' and take the pull request title and description into account when writing the response.\n\n"
                "Git diff to review:\n\n"
                f"```diff\n{diff_text}\n```\n\n"
            #    "File content for reference:\n\n"
            #    f"```code\n{file_content}\n```\n"
                "Ensure that all your responses are in Korean. \n"
    )

    body = json.dumps({
        # "prompt" : f'Please review the following code:\n{diff_text}'
        "prompt" : prompt
    })
    response = bedrock_client.invoke_model(
        modelId='meta.llama3-70b-instruct-v1:0',
        body=body
    )

    model_response = json.loads(response["body"].read())

    # Extract and print the response text.
    response_text = model_response["generation"]

    print(response_text)

    return response_text

def post_review_comment(repo_name, pr_number, review_comment):
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(review_comment)

def main(repo_name, pr_number):
    diff_text = get_pr_diff(repo_name, pr_number)
    review_comment = generate_review(diff_text)
    if review_comment:
        print(review_comment)
        #post_review_comment(repo_name, pr_number, review_comment)

if __name__ == "__main__":
    # GitHub 리포지토리 이름과 PR 번호를 입력하세요.
    repo_name = "llm-ai-codereview/react-sample"
    pr_number = 1  # 예: 1
    main(repo_name, pr_number)
