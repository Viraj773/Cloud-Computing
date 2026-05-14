import json
import os
import boto3

REGION_NAME = os.environ.get("AWS_REGION", "us-east-1")
LOGIN_TABLE = os.environ.get("LOGIN_TABLE", "login")

dynamodb    = boto3.resource("dynamodb", region_name=REGION_NAME)
login_table = dynamodb.Table(LOGIN_TABLE)

CORS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Content-Type": "application/json"
}

def respond(status, body):
    return {"statusCode": status, "headers": CORS, "body": json.dumps(body)}

def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return respond(200, {})

    try:
        body_raw = event.get("body") or ""
        body = json.loads(body_raw)
        email     = body.get("email",     "").strip()
        user_name = body.get("user_name", "").strip()
        password  = body.get("password",  "").strip()

        if not email or not user_name or not password:
            return respond(400, {"error": "All fields are required"})

        existing = login_table.get_item(Key={"email": email}).get("Item")
        if existing:
            return respond(409, {"error": "The email already exists"})

        login_table.put_item(
            Item={"email": email, "user_name": user_name, "password": password}
        )
        return respond(201, {"message": "Registered successfully"})

    except Exception as exc:
        print(f"ERROR: {exc}")
        return respond(500, {"error": "Internal server error"})
