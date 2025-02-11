#!/bin/bash

# Configuration
AWS_REGION="us-east-1"
ECR_REPOSITORY="video-processor"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Create ECR repository if it doesn't exist
aws ecr create-repository --repository-name ${ECR_REPOSITORY} --region ${AWS_REGION} || true

# Build and push each Lambda function
for function in video_processor upload_handler notification_handler; do
    echo "Building ${function}..."
    
    # Build the Docker image
    docker build -t ${ECR_REPOSITORY}:${function} ./lambda/${function}/
    
    # Tag the image for ECR
    docker tag ${ECR_REPOSITORY}:${function} ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${function}
    
    # Push to ECR
    docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${function}
    
    echo "${function} built and pushed successfully"
done

echo "All images built and pushed successfully"