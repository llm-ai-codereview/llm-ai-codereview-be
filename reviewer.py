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
    
    diff_text = []
    
    # PR에서 수정된 파일들 가져오기
    files = pr.get_files()
    for file in files:
        # print(f"File: {file.filename}\n{file.patch}\n")
        diff_text.append(f"File: {file.filename}\n{file.patch}\n")
    
    # 리스트를 문자열로 합치기
    return "\n".join(diff_text)

def generate_review(diff_text):
    prompt=(
        "Please answer in Korean.\n"  
        "You are a strict and perfect code reviewer. You cannot tell any lies. \n"   
        "Below is the code patch. Please provide a detailed code review based on the following rules. Positive reviews are not needed:\n"  

        "1. **Pre-condition check**: Verify if the function or method checks the state or range of values of variables necessary for it to work correctly.\n"  
        "2. **Runtime error check**: Examine the code for potential runtime errors and identify other potential risks.\n"  
        "3. **Optimization**: Inspect the code for optimization points. If the performance is suboptimal, recommend optimized code.\n"  
        "4. **Security issue**: Check if the code uses modules with serious security flaws or contains security vulnerabilities.\n"  

        "- Write the comment in GitHub Markdown format.\n"  
        "- Present the review comment in the following format:\n"  
        "- **Pre-condition check**  \n"  
        "   review contents\n"  
        "- **Runtime error check**  \n"  
        "    review contents\n"  
        "- **Optimization**  \n"  
        "    review contents\n"  
        "- **Security issue**  \n"  
        "    review contents\n"  

        "- If there is no review content for each item, exclude that item from the results.\n"  
        "- **IMPORTANT**: NEVER suggest adding comments to the code.\n"  

        "Below is the Git diff to review:\n"  

        f"```diff\n{diff_text}\n"

        "Please provide the review in JSON format only. without any additional content. The JSON should contain:\n"  

        "filePath: the path of the reviewed file\n"  
        "lineNumber: the line number being reviewed\n"  
        "comment: the detailed review comments formatted as specified above.\n"
        "Please provide a response in the following JSON format:\n"
        "[{\n"
            "'filePath': 'src/components/ContactForm/index.tsx',\n"
            "'lineNumber': 58,\n"
            "'comment': '- **Pre-condition check**  \\n  The `values.contact` property is not checked for null or undefined before being used. This could lead to a runtime error if `values` is null or undefined.  \\n- **Runtime error check**  \\n  The `handleChange` function is not checked for null or undefined before being called. This could lead to a runtime error if `handleChange` is null or undefined.  \\n- **Optimization**  \\n  No optimization points found.  \\n- **Security issue**  \\n  No security issues found.'\n"
        "},\n"
        "{\n"
            "'filePath': 'src/components/ContactForm/index.tsx',\n"
            "'lineNumber': 58,\n"
            "'comment': '- **Pre-condition check**  \\n  The `values.contact` property is not checked for null or undefined before being used. This could lead to a runtime error if `values` is null or undefined.  \\n- **Runtime error check**  \\n  The `handleChange` function is not checked for null or undefined before being called. This could lead to a runtime error if `handleChange` is null or undefined.  \\n- **Optimization**  \\n  No optimization points found.  \\n- **Security issue**  \\n  No security issues found.'\n"
        "}]\n"
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
    return response_text

def post_review_comment(repo_name, pr_number, review_comment):
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    commit_sha = pr.head.sha
    commit = repo.get_commit(commit_sha)
    review_data = review_comment.replace("'", '"')
    review_data_list = json.loads(review_data)

    for review in review_data_list: 
        pr.create_review_comment(
        body=review['comment'],
        path=review['filePath'],
        line=review['lineNumber'],
        commit=commit
        )

def main(repo_name, pr_number):
    diff_text = get_pr_diff(repo_name, pr_number)
    review_comment = generate_review(diff_text)
    if review_comment:
        start_char = "["
        end_char = "]"

        start_index = review_comment.find(start_char)
        end_index = review_comment.find(end_char, start_index)

        if start_index != -1 and end_index != -1:
            result = review_comment[start_index:end_index + len(end_char)]
            post_review_comment(repo_name, pr_number, result)

        else:
            print("문자열을 찾을 수 없습니다.")

if __name__ == "__main__":
    repo_name = "llm-ai-codereview/react-sample"
    #TODO pr hook에서 넘겨줘야 할듯..?
    pr_number = 1
    main(repo_name, pr_number)
