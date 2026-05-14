import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

REGION_NAME         = os.environ.get("AWS_REGION", "us-east-1")
SUBSCRIPTIONS_TABLE = os.environ.get("SUBSCRIPTIONS_TABLE", "subscriptions")
BUCKET_NAME         = os.environ.get("BUCKET_NAME", "s4106671-mybucket")

dynamodb  = boto3.resource("dynamodb", region_name=REGION_NAME)
sub_table = dynamodb.Table(SUBSCRIPTIONS_TABLE)
s3_client = boto3.client("s3", region_name=REGION_NAME)

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-User-Email",
    "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
    "Content-Type": "application/json"
}

def respond(status, body):
    return {"statusCode": status, "headers": CORS, "body": json.dumps(body)}

def get_email(event):
    qs = event.get("queryStringParameters") or {}
    email = qs.get("email", "").strip()
    if email:
        return email
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    return headers.get("x-user-email", "").strip()

def get_presigned_url(song):
    s3_key = song.get("s3_key")
    if not s3_key and song.get("img_url"):
        filename = song["img_url"].split("/")[-1]
        s3_key = f"artist-images/{filename}"
    if not s3_key:
        return ""
    try:
        return s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": s3_key},
            ExpiresIn=3600,
        )
    except ClientError:
        return ""

def make_song_id(title, album, year):
    return f"{title}#{album}#{year}"

def handle_get(email):
    resp = sub_table.query(KeyConditionExpression=Key("email").eq(email))
    items = resp.get("Items", [])
    for item in items:
        item["presigned_url"] = get_presigned_url(item)
    return respond(200, {"subscriptions": items})

def handle_post(email, body):
    title   = body.get("title", "")
    artist  = body.get("artist", "")
    year    = body.get("year", "")
    album   = body.get("album", "")
    img_url = body.get("img_url", "")
    s3_key  = body.get("s3_key") or (f"artist-images/{img_url.split('/')[-1]}" if img_url else "")
    song_id = body.get("song_id") or make_song_id(title, album, year)
    if not title or not artist:
        return respond(400, {"error": "title and artist required"})
    sub_table.put_item(Item={
        "email": email, "song_id": song_id, "title": title,
        "artist": artist, "year": year, "album": album,
        "img_url": img_url, "s3_key": s3_key,
    })
    return respond(201, {"message": "Subscribed"})

def handle_delete(email, body):
    song_id = body.get("song_id", "")
    if not song_id:
        return respond(400, {"error": "song_id required"})
    sub_table.delete_item(Key={"email": email, "song_id": song_id})
    return respond(200, {"message": "Removed"})

def handler(event, context):
    method = event.get("httpMethod", "GET")
    if method == "OPTIONS":
        return respond(200, {})
    email = get_email(event)
    if not email:
        return respond(401, {"error": "Email missing"})
    try:
        if method == "GET":
            return handle_get(email)
        body_raw = event.get("body") or "{}"
        try:
            body = json.loads(body_raw)
        except:
            from urllib.parse import parse_qs
            p = parse_qs(body_raw)
            body = {k: v[0] for k, v in p.items()}
        if method == "POST":
            return handle_post(email, body)
        if method == "DELETE":
            return handle_delete(email, body)
        return respond(405, {"error": f"Method {method} not allowed"})
    except Exception as exc:
        print(f"ERROR: {exc}")
        return respond(500, {"error": "Internal server error"})
