import os
from flask import Flask, render_template, request, redirect, url_for, session
import boto3
from boto3.dynamodb.conditions import Key, Attr

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "musicapp2026")

REGION_NAME = os.environ.get("AWS_REGION", "us-east-1")

# On ECS Fargate the task role (LabRole) provides credentials automatically.
# boto3 picks them up from the ECS metadata endpoint — no keys needed in code.
dynamodb = boto3.resource("dynamodb", region_name=REGION_NAME)
s3       = boto3.client("s3",         region_name=REGION_NAME)

BUCKET_NAME         = os.environ.get("BUCKET_NAME",         "s4106671-mybucket")
LOGIN_TABLE         = os.environ.get("LOGIN_TABLE",         "login")
MUSIC_TABLE         = os.environ.get("MUSIC_TABLE",         "music")
SUBSCRIPTIONS_TABLE = os.environ.get("SUBSCRIPTIONS_TABLE", "subscriptions")


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_song_id(title, album, year):
    return f"{title}#{album}#{year}"


def make_s3_key_from_img_url(img_url):
    filename = img_url.split("/")[-1]
    return f"artist-images/{filename}"


def get_presigned_url(song):
    s3_key = song.get("s3_key")
    if not s3_key and song.get("img_url"):
        s3_key = make_s3_key_from_img_url(song["img_url"])
    if not s3_key:
        return ""
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET_NAME, "Key": s3_key},
        ExpiresIn=3600,
    )


def add_presigned_urls(songs):
    for song in songs:
        song["presigned_url"] = get_presigned_url(song)
    return songs


def get_user_subscriptions(email):
    sub_table = dynamodb.Table(SUBSCRIPTIONS_TABLE)
    response  = sub_table.query(
        KeyConditionExpression=Key("email").eq(email)
    )
    return add_presigned_urls(response.get("Items", []))


# ── Routes (identical to EC2 app.py) ─────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email    = request.form["email"].strip()
        password = request.form["password"].strip()
        response = dynamodb.Table(LOGIN_TABLE).get_item(Key={"email": email})
        user     = response.get("Item")
        if user and user["password"] == password:
            session["email"]    = email
            session["username"] = user["user_name"]
            return redirect(url_for("main"))
        error = "email or password is invalid"
    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        email    = request.form["email"].strip()
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        login_table = dynamodb.Table(LOGIN_TABLE)
        if login_table.get_item(Key={"email": email}).get("Item"):
            error = "The email already exists"
        else:
            login_table.put_item(
                Item={"email": email, "user_name": username, "password": password}
            )
            return redirect(url_for("login"))
    return render_template("register.html", error=error)


@app.route("/main")
def main():
    if "email" not in session:
        return redirect(url_for("login"))
    return render_template(
        "main.html",
        username=session["username"],
        subscriptions=get_user_subscriptions(session["email"]),
        query_results=None,
        query_message=None,
    )


@app.route("/query", methods=["POST"])
def query():
    if "email" not in session:
        return redirect(url_for("login"))

    title  = request.form.get("title",  "").strip()
    artist = request.form.get("artist", "").strip()
    year   = request.form.get("year",   "").strip()
    album  = request.form.get("album",  "").strip()
    subscriptions = get_user_subscriptions(session["email"])

    if not any([title, artist, year, album]):
        return render_template(
            "main.html",
            username=session["username"],
            subscriptions=subscriptions,
            query_results=[],
            query_message="Please enter at least one search field.",
        )

    music_table   = dynamodb.Table(MUSIC_TABLE)
    query_results = []

    if artist and album:
        resp = music_table.query(
            IndexName="artist-album-index",
            KeyConditionExpression=Key("artist").eq(artist) & Key("album").eq(album),
        )
        query_results = resp.get("Items", [])
        if title:
            query_results = [s for s in query_results if s.get("title") == title]
        if year:
            query_results = [s for s in query_results if s.get("year") == year]

    elif artist:
        resp = music_table.query(KeyConditionExpression=Key("artist").eq(artist))
        query_results = resp.get("Items", [])
        if title:
            query_results = [s for s in query_results if s.get("title") == title]
        if year:
            query_results = [s for s in query_results if s.get("year") == year]
        if album:
            query_results = [s for s in query_results if s.get("album") == album]

    elif title:
        kce = Key("title").eq(title)
        if year:
            kce = kce & Key("year").eq(year)
        resp = music_table.query(IndexName="title-year-index", KeyConditionExpression=kce)
        query_results = resp.get("Items", [])
        if album:
            query_results = [s for s in query_results if s.get("album") == album]

    else:
        filter_parts = []
        if year:
            filter_parts.append(Attr("year").eq(year))
        if album:
            filter_parts.append(Attr("album").eq(album))
        fe = filter_parts[0]
        for c in filter_parts[1:]:
            fe = fe & c
        resp = music_table.scan(FilterExpression=fe)
        query_results = resp.get("Items", [])

    query_results = add_presigned_urls(query_results)
    query_message = "No result is retrieved. Please query again" if not query_results else None

    return render_template(
        "main.html",
        username=session["username"],
        subscriptions=subscriptions,
        query_results=query_results,
        query_message=query_message,
    )


@app.route("/subscribe", methods=["POST"])
def subscribe():
    if "email" not in session:
        return redirect(url_for("login"))
    title   = request.form["title"]
    artist  = request.form["artist"]
    year    = request.form["year"]
    album   = request.form["album"]
    img_url = request.form["img_url"]
    s3_key  = request.form.get("s3_key") or make_s3_key_from_img_url(img_url)
    song_id = request.form.get("song_id") or make_song_id(title, album, year)
    dynamodb.Table(SUBSCRIPTIONS_TABLE).put_item(
        Item={
            "email":   session["email"],
            "song_id": song_id,
            "title":   title,
            "artist":  artist,
            "year":    year,
            "album":   album,
            "img_url": img_url,
            "s3_key":  s3_key,
        }
    )
    return redirect(url_for("main"))


@app.route("/remove", methods=["POST"])
def remove():
    if "email" not in session:
        return redirect(url_for("login"))
    dynamodb.Table(SUBSCRIPTIONS_TABLE).delete_item(
        Key={"email": session["email"], "song_id": request.form["song_id"]}
    )
    return redirect(url_for("main"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/health")
def health():
    return {"status": "ok", "backend": "ECS"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)
