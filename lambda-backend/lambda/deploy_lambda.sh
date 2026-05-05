#!/bin/bash
# deploy_lambda.sh — package and deploy all four Lambda functions
# Run from the lambda/ directory.
set -euo pipefail

REGION="us-east-1"
RUNTIME="python3.12"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/LabRole"

BUCKET="s4098345-mybucket"

# name → handler
declare -A FUNCTIONS=(
  ["music-app-login"]="lambda_login.handler"
  ["music-app-register"]="lambda_register.handler"
  ["music-app-query"]="lambda_query.handler"
  ["music-app-subscriptions"]="lambda_subscriptions.handler"
)

declare -A SOURCE=(
  ["music-app-login"]="functions/lambda_login.py"
  ["music-app-register"]="functions/lambda_register.py"
  ["music-app-query"]="functions/lambda_query.py"
  ["music-app-subscriptions"]="functions/lambda_subscriptions.py"
)

ENV_VARS="Variables={AWS_REGION=${REGION},BUCKET_NAME=${BUCKET},LOGIN_TABLE=login,MUSIC_TABLE=music,SUBSCRIPTIONS_TABLE=subscriptions}"

TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

for NAME in "${!FUNCTIONS[@]}"; do
  HANDLER="${FUNCTIONS[$NAME]}"
  SRC="${SOURCE[$NAME]}"
  ZIP="${TMP}/${NAME}.zip"

  echo "--- ${NAME} ---"
  zip -j "$ZIP" "$SRC"

  if aws lambda get-function --function-name "$NAME" --region "$REGION" &>/dev/null; then
    aws lambda update-function-code \
      --function-name "$NAME" \
      --zip-file "fileb://${ZIP}" \
      --region "$REGION" > /dev/null
    aws lambda update-function-configuration \
      --function-name "$NAME" \
      --environment "$ENV_VARS" \
      --region "$REGION" > /dev/null
    echo "  Updated."
  else
    aws lambda create-function \
      --function-name  "$NAME" \
      --runtime        "$RUNTIME" \
      --role           "$ROLE_ARN" \
      --handler        "$HANDLER" \
      --zip-file       "fileb://${ZIP}" \
      --timeout        30 \
      --memory-size    256 \
      --environment    "$ENV_VARS" \
      --region         "$REGION" > /dev/null
    echo "  Created."
  fi
done

echo ""
echo "=== All Lambda functions deployed ==="
echo ""
echo "API Gateway resource mapping:"
echo "  POST   /login           → music-app-login"
echo "  POST   /register        → music-app-register"
echo "  GET    /query           → music-app-query"
echo "  GET    /subscriptions   → music-app-subscriptions"
echo "  POST   /subscriptions   → music-app-subscriptions"
echo "  DELETE /subscriptions   → music-app-subscriptions"
echo ""
echo "Enable Lambda Proxy Integration and CORS on each resource, then deploy to stage 'prod'."
