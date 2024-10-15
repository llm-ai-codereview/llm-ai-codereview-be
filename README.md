# llm-ai-codereview-be

pipenv --python 3.9
pipenv install 패키지명 // dependency 패키지 설치
pipenv shell // 가상환경 실행
exit // 가상환경 종료
pipenv --rm // 가상환경 삭제

```
export AWS_ACCESS_KEY='your_aws_access_key'
export AWS_SECRET_KEY='your_aws_secret_key'
export GITHUB_TOKEN='your_github_token'
```

---API 호출 예시---
flask run 실행 후 
POST http://127.0.0.1:5000/review
{
    "repo_name":"llm-ai-codereview/react-sample",
    "pr_number":2
}
호출