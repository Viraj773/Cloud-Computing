import json
import os
import boto3

REGION_NAME = os.environ.get("AWS_REGION", "us-east-1")
LOGIN_TABLE  = os.environ.get("LOGIN_TABLE", "login")

dynamodb    = boto3.resource("dynamodb", region_name=REGION_NAME)
login_table = dynamodb.Table(LOGIN_TABLE)

CORS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}


def respond(status, body):
    return {
        "statusCode": status,
        "headers":    {**CORS, "Content-Type": "application/json"},
        "body":       json.dumps(body),
    }


def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return respond(200, {})

    body_raw = event.get("body") or ""

    try:
        body     = json.loads(body_raw)
        email    = body.get("email",    "").strip()
        password = body.get("password", "").strip()
    except Exception:
        return respond(400, {"error": "Invalid JSON body"})

    if not email or not password:
        return respond(400, {"error": "email and password required"})

    resp = login_table.get_item(Key={"email": email})
    user = resp.get("Item")

    if not user or user.get("password") != password:
        return respond(401, {"error": "email or password is invalid"})

    return respond(200, {
        "email":     user["email"],
        "user_name": user["user_name"],
    })
