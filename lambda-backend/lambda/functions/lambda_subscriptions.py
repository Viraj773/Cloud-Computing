"""
lambda_subscriptions.py  —  GET / POST / DELETE /subscriptions
Maps to subscribe(), remove(), and get_user_subscriptions() in app.py.

One Lambda handles all three HTTP methods so API Gateway has a single
integration — avoids duplicating DynamoDB logic across multiple functions.

Method mapping (configured in API Gateway):
  GET    /subscriptions          → list subscriptions for a user
  POST   /subscriptions          → add a subscription  (maps to /subscribe)
  DELETE /subscriptions          → remove a subscription  (maps to /remove)
"""
import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

REGION_NAME         = os.environ.get("AWS_REGION",             "us-east-1")
SUBSCRIPTIONS_TABLE = os.environ.get("SUBSCRIPTIONS_TABLE",    "subscriptions")
BUCKET_NAME         = os.environ.get("BUCKET_NAME",            "s4098345-mybucket")

dynamodb  = boto3.resource("dynamodb", region_name=REGION_NAME)
s3        = boto3.client("s3",         region_name=REGION_NAME)
sub_table = dynamodb.Table(SUBSCRIPTIONS_TABLE)

CORS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Headers": "Content-Type,X-User-Email",
    "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
}


def respond(status, body):
    return {
        "statusCode": status,
        "headers":    {**CORS, "Content-Type": "application/json"},
        "body":       json.dumps(body),
    }


def get_email(event):
    """
    The frontend sends the logged-in user's email via a custom header.
    For session-based frontends the header is set after login.
    """
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    return headers.get("x-user-email", "").strip()


def get_presigned_url(song):
    s3_key = song.get("s3_key")
    if not s3_key and song.get("img_url"):
        filename = song["img_url"].split("/")[-1]
        s3_key   = f"artist-images/{filename}"
    if not s3_key:
        return ""
    try:
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": s3_key},
            ExpiresIn=3600,
        )
    except ClientError:
        return ""


def make_song_id(title, album, year):
    """Must match music.py — title#album#year."""
    return f"{title}#{album}#{year}"


# ── GET — list subscriptions ──────────────────────────────────────────────────
def handle_get(email):
    # Query on partition key — O(1), no Scan needed
    resp  = sub_table.query(KeyConditionExpression=Key("email").eq(email))
    songs = resp.get("Items", [])
    for song in songs:
        song["presigned_url"] = get_presigned_url(song)
    return respond(200, {"subscriptions": songs})


# ── POST — subscribe ──────────────────────────────────────────────────────────
def handle_post(email, body):
    title   = body.get("title",   "")
    artist  = body.get("artist",  "")
    year    = body.get("year",    "")
    album   = body.get("album",   "")
    img_url = body.get("img_url", "")
    s3_key  = body.get("s3_key") or (
        f"artist-images/{img_url.split('/')[-1]}" if img_url else ""
    )
    song_id = body.get("song_id") or make_song_id(title, album, year)

    if not title or not artist:
        return respond(400, {"error": "title and artist are required"})

    sub_table.put_item(Item={
        "email":   email,
        "song_id": song_id,
        "title":   title,
        "artist":  artist,
        "year":    year,
        "album":   album,
        "img_url": img_url,
        "s3_key":  s3_key,
    })
    return respond(201, {"message": "Subscribed"})


# ── DELETE — remove subscription ──────────────────────────────────────────────
def handle_delete(email, body):
    song_id = body.get("song_id", "")
    if not song_id:
        return respond(400, {"error": "song_id is required"})
    # delete_item by composite key — O(1)
    sub_table.delete_item(Key={"email": email, "song_id": song_id})
    return respond(200, {"message": "Removed"})


# ── Entry point ───────────────────────────────────────────────────────────────
def handler(event, context):
    method = event.get("httpMethod", "GET")

    if method == "OPTIONS":
        return respond(200, {})

    email = get_email(event)
    if not email:
        return respond(401, {"error": "X-User-Email header missing — please log in"})

    if method == "GET":
        return handle_get(email)

    body_raw = event.get("body") or "{}"
    try:
        body = json.loads(body_raw)
    except json.JSONDecodeError:
        from urllib.parse import parse_qs
        p    = parse_qs(body_raw)
        body = {k: v[0] for k, v in p.items()}

    if method == "POST":
        return handle_post(email, body)

    if method == "DELETE":
        return handle_delete(email, body)

    return respond(405, {"error": f"Method {method} not allowed"})
