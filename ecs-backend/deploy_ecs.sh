#!/bin/bash
# deploy_ecs.sh — build image, push to ECR, update ECS Fargate service
# Run from the ecs/ directory after filling in your cluster/service names.
set -euo pipefail

REGION="us-east-1"
REPO="music-app"
CLUSTER="music-app-cluster"   # your ECS cluster name
SERVICE="music-app-service"   # your ECS service name
LOG_GROUP="/ecs/music-app"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO}"

echo "Account: $ACCOUNT_ID"

# Create ECR repo if absent
aws ecr describe-repositories --repository-names "$REPO" --region "$REGION" 2>/dev/null \
  || aws ecr create-repository --repository-name "$REPO" --region "$REGION"

# Docker login
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

# Build and push
docker build -t "${REPO}:latest" .
docker tag  "${REPO}:latest" "${ECR_URI}:latest"
docker push "${ECR_URI}:latest"
echo "Pushed: ${ECR_URI}:latest"

# Ensure CloudWatch log group exists
aws logs create-log-group --log-group-name "$LOG_GROUP" --region "$REGION" 2>/dev/null || true

# Patch account ID into task definition and register it
sed "s/ACCOUNT_ID/${ACCOUNT_ID}/g" task-definition.json > /tmp/task-def.json
TASK_ARN=$(aws ecs register-task-definition \
  --cli-input-json file:///tmp/task-def.json \
  --query "taskDefinition.taskDefinitionArn" --output text)
echo "Task definition: $TASK_ARN"

# Update running service with the new task definition
aws ecs update-service \
  --cluster "$CLUSTER" \
  --service "$SERVICE" \
  --task-definition "$TASK_ARN" \
  --force-new-deployment \
  --region "$REGION"

echo "ECS service updated. New tasks will start shortly."
