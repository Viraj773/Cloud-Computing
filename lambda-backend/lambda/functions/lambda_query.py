"""
lambda_query.py  —  GET /query?title=&artist=&year=&album=
Maps to the query() route in app.py.
Uses the same Query/Scan strategy:
  artist + album  → LSI  artist-album-index
  artist only     → main table PK Query
  title [+ year]  → GSI  title-year-index
  year / album    → Scan with FilterExpression
"""
import json
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

REGION_NAME         = os.environ.get("AWS_REGION",     "us-east-1")
MUSIC_TABLE         = os.environ.get("MUSIC_TABLE",     "music")
BUCKET_NAME         = os.environ.get("BUCKET_NAME",     "s4098345-mybucket")

dynamodb    = boto3.resource("dynamodb", region_name=REGION_NAME)
s3          = boto3.client("s3",         region_name=REGION_NAME)
music_table = dynamodb.Table(MUSIC_TABLE)

CORS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Headers": "Content-Type,X-User-Email",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
}


def respond(status, body):
    return {
        "statusCode": status,
        "headers":    {**CORS, "Content-Type": "application/json"},
        "body":       json.dumps(body),
    }


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


def add_presigned_urls(songs):
    for song in songs:
        song["presigned_url"] = get_presigned_url(song)
    return songs


def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return respond(200, {})

    qs     = event.get("queryStringParameters") or {}
    title  = qs.get("title",  "").strip()
    artist = qs.get("artist", "").strip()
    year   = qs.get("year",   "").strip()
    album  = qs.get("album",  "").strip()

    if not any([title, artist, year, album]):
        return respond(400, {"error": "Please enter at least one search field."})

    results = []

    # Case 1: artist + album → LSI
    if artist and album:
        resp    = music_table.query(
            IndexName="artist-album-index",
            KeyConditionExpression=Key("artist").eq(artist) & Key("album").eq(album),
        )
        results = resp.get("Items", [])
        if title:
            results = [s for s in results if s.get("title") == title]
        if year:
            results = [s for s in results if s.get("year") == year]

    # Case 2: artist only → PK Query
    elif artist:
        resp    = music_table.query(KeyConditionExpression=Key("artist").eq(artist))
        results = resp.get("Items", [])
        if title:
            results = [s for s in results if s.get("title") == title]
        if year:
            results = [s for s in results if s.get("year") == year]
        if album:
            results = [s for s in results if s.get("album") == album]

    # Case 3: title [+ year] → GSI
    elif title:
        kce  = Key("title").eq(title)
        if year:
            kce = kce & Key("year").eq(year)
        resp    = music_table.query(IndexName="title-year-index", KeyConditionExpression=kce)
        results = resp.get("Items", [])
        if album:
            results = [s for s in results if s.get("album") == album]

    # Case 4: year / album only → Scan
    else:
        filter_parts = []
        if year:
            filter_parts.append(Attr("year").eq(year))
        if album:
            filter_parts.append(Attr("album").eq(album))
        fe = filter_parts[0]
        for c in filter_parts[1:]:
            fe = fe & c
        resp    = music_table.scan(FilterExpression=fe)
        results = resp.get("Items", [])

    results = add_presigned_urls(results)

    if not results:
        return respond(200, {
            "songs":   [],
            "message": "No result is retrieved. Please query again",
        })

    return respond(200, {"songs": results})
