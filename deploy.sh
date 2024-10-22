#!/bin/bash

# 이미지 이름 및 태그 설정
IMAGE_NAME="llm-code-review-image"

# 1. 기존 이미지 삭제 (선택 사항, 필요 없다면 생략)
# docker rmi $IMAGE_NAME:latest

# 2. 새 이미지 빌드
docker build -t $IMAGE_NAME .

# 3. 태그 지정 (이미 존재하면 덮어쓰기)
docker tag $IMAGE_NAME:latest 813990269506.dkr.ecr.us-east-1.amazonaws.com/llm-code-review-repo:latest

# 4. ECR에 이미지 푸시
docker push 813990269506.dkr.ecr.us-east-1.amazonaws.com/llm-code-review-repo:latest

# 5. Lambda 함수 업데이트 (AWS CLI 사용)
aws lambda update-function-code --function-name llm-code-review \
    --image-uri 813990269506.dkr.ecr.us-east-1.amazonaws.com/llm-code-review-repo:latest
