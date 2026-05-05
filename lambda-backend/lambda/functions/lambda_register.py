"""
lambda_register.py  —  POST /register
Maps to the register() route in app.py.
"""
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


def parse_body(event):
    content_type = (event.get("headers") or {}).get("Content-Type", "")
    body_raw     = event.get("body") or ""
    if "application/json" in content_type:
        b = json.loads(body_raw)
        return b.get("email", "").strip(), b.get("username", "").strip(), b.get("password", "").strip()
    from urllib.parse import parse_qs
    p = parse_qs(body_raw)
    return (
        p.get("email",    [""])[0].strip(),
        p.get("username", [""])[0].strip(),
        p.get("password", [""])[0].strip(),
    )


def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return respond(200, {})

    email, username, password = parse_body(event)

    if not email or not username or not password:
        return respond(400, {"error": "All fields are required"})

    # Check for existing email — get_item is O(1) on partition key
    existing = login_table.get_item(Key={"email": email}).get("Item")
    if existing:
        # Exact error message required by spec
        return respond(409, {"error": "The email already exists"})

    login_table.put_item(
        Item={"email": email, "user_name": username, "password": password}
    )
    return respond(201, {"message": "Registered successfully"})
