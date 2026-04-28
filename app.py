from flask import Flask, render_template, request, redirect, url_for, session
import boto3
from boto3.dynamodb.conditions import Key, Attr

app = Flask(__name__)
app.secret_key = "musicapp2026"

REGION_NAME = "us-east-1"

AWS_ACCESS_KEY_ID = "PASTE_ACCESS_KEY_HERE"
AWS_SECRET_ACCESS_KEY = "PASTE_SECRET_KEY_HERE"
AWS_SESSION_TOKEN = "PASTE_SESSION_TOKEN_HERE"


def using_placeholder_credentials():
    return (
        AWS_ACCESS_KEY_ID == "PASTE_ACCESS_KEY_HERE"
        or AWS_SECRET_ACCESS_KEY == "PASTE_SECRET_KEY_HERE"
        or AWS_SESSION_TOKEN == "PASTE_SESSION_TOKEN_HERE"
    )


if using_placeholder_credentials():
    # On EC2 boto3 automatically uses LabInstanceProfile/LabRole
    dynamodb = boto3.resource("dynamodb", region_name=REGION_NAME)
    s3 = boto3.client("s3", region_name=REGION_NAME)
else:
    # For local testing we can paste the temporary AWS academy credentials above
    dynamodb = boto3.resource(
        "dynamodb",
        region_name=REGION_NAME,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )

    s3 = boto3.client(
        "s3",
        region_name=REGION_NAME,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )

BUCKET_NAME = "s4098345-mybucket"

LOGIN_TABLE = "login"
MUSIC_TABLE = "music"
SUBSCRIPTIONS_TABLE = "subscriptions"


# HELPER FUNCTIONS

def make_song_id(title, album, year):
    # This matches the song_id created in music.py
    return f"{title}#{album}#{year}"


def make_s3_key_from_img_url(img_url):
    # Converts original image URL into the S3 path used in music.py
    filename = img_url.split("/")[-1]
    return f"artist-images/{filename}"


def get_image_url(song):
    # Creates a temporary secure S3 image URL
    s3_key = song.get("s3_key")

    if not s3_key and song.get("img_url"):
        s3_key = make_s3_key_from_img_url(song["img_url"])

    if not s3_key:
        return ""

    return s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": s3_key
        },
        ExpiresIn=3600
    )


def add_presigned_urls(songs):
    # Adds image links before sending songs to the HTML page
    for song in songs:
        song["presigned_url"] = get_image_url(song)
    return songs


def get_user_subscriptions(email):
    # Query is used here because email is the partition key
    sub_table = dynamodb.Table(SUBSCRIPTIONS_TABLE)

    response = sub_table.query(
        KeyConditionExpression=Key("email").eq(email)
    )

    return add_presigned_urls(response.get("Items", []))


# LOGIN PAGE

@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        login_table = dynamodb.Table(LOGIN_TABLE)

        response = login_table.get_item(
            Key={
                "email": email
            }
        )

        user = response.get("Item")

        if user and user["password"] == password:
            session["email"] = email
            session["username"] = user["user_name"]
            return redirect(url_for("main"))

        error = "email or password is invalid"

    return render_template("login.html", error=error)


# REGISTER PAGE

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        email = request.form["email"].strip()
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        login_table = dynamodb.Table(LOGIN_TABLE)

        response = login_table.get_item(
            Key={
                "email": email
            }
        )

        existing_user = response.get("Item")

        if existing_user:
            error = "The email already exists"
        else:
            login_table.put_item(
                Item={
                    "email": email,
                    "user_name": username,
                    "password": password
                }
            )

            return redirect(url_for("login"))

    return render_template("register.html", error=error)


# MAIN PAGE

@app.route("/main")
def main():
    if "email" not in session:
        return redirect(url_for("login"))

    subscriptions = get_user_subscriptions(session["email"])

    return render_template(
        "main.html",
        username=session["username"],
        subscriptions=subscriptions,
        query_results=None,
        query_message=None
    )


# QUERY SONGS

@app.route("/query", methods=["POST"])
def query():
    if "email" not in session:
        return redirect(url_for("login"))

    title = request.form.get("title", "").strip()
    artist = request.form.get("artist", "").strip()
    year = request.form.get("year", "").strip()
    album = request.form.get("album", "").strip()

    subscriptions = get_user_subscriptions(session["email"])

    if not any([title, artist, year, album]):
        return render_template(
            "main.html",
            username=session["username"],
            subscriptions=subscriptions,
            query_results=[],
            query_message="Please enter at least one search field."
        )

    music_table = dynamodb.Table(MUSIC_TABLE)
    query_results = []

    # Case 1: Artist + album search uses the LSI
    if artist and album:
        response = music_table.query(
            IndexName="artist-album-index",
            KeyConditionExpression=Key("artist").eq(artist) & Key("album").eq(album)
        )

        query_results = response.get("Items", [])

        if title:
            query_results = [song for song in query_results if song.get("title") == title]
        if year:
            query_results = [song for song in query_results if song.get("year") == year]

    # Case 2: Artist search uses the main table partition key
    elif artist:
        response = music_table.query(
            KeyConditionExpression=Key("artist").eq(artist)
        )

        query_results = response.get("Items", [])

        if title:
            query_results = [song for song in query_results if song.get("title") == title]
        if year:
            query_results = [song for song in query_results if song.get("year") == year]
        if album:
            query_results = [song for song in query_results if song.get("album") == album]

    # Case 3: Title search uses the GSI
    elif title:
        if year:
            response = music_table.query(
                IndexName="title-year-index",
                KeyConditionExpression=Key("title").eq(title) & Key("year").eq(year)
            )
        else:
            response = music_table.query(
                IndexName="title-year-index",
                KeyConditionExpression=Key("title").eq(title)
            )

        query_results = response.get("Items", [])

        if album:
            query_results = [song for song in query_results if song.get("album") == album]

    # Case 4: Year-only or album-only search uses Scan as fallback
    else:
        filter_parts = []

        if year:
            filter_parts.append(Attr("year").eq(year))
        if album:
            filter_parts.append(Attr("album").eq(album))

        filter_expression = filter_parts[0]

        for condition in filter_parts[1:]:
            filter_expression = filter_expression & condition

        response = music_table.scan(
            FilterExpression=filter_expression
        )

        query_results = response.get("Items", [])

    query_results = add_presigned_urls(query_results)

    query_message = None
    if not query_results:
        query_message = "No result is retrieved. Please query again"

    return render_template(
        "main.html",
        username=session["username"],
        subscriptions=subscriptions,
        query_results=query_results,
        query_message=query_message
    )


# SUBSCRIBE TO A SONG

@app.route("/subscribe", methods=["POST"])
def subscribe():
    if "email" not in session:
        return redirect(url_for("login"))

    title = request.form["title"]
    artist = request.form["artist"]
    year = request.form["year"]
    album = request.form["album"]
    img_url = request.form["img_url"]
    s3_key = request.form.get("s3_key", make_s3_key_from_img_url(img_url))

    song_id = request.form.get("song_id") or make_song_id(title, album, year)

    sub_table = dynamodb.Table(SUBSCRIPTIONS_TABLE)

    sub_table.put_item(
        Item={
            "email": session["email"],
            "song_id": song_id,
            "title": title,
            "artist": artist,
            "year": year,
            "album": album,
            "img_url": img_url,
            "s3_key": s3_key
        }
    )

    return redirect(url_for("main"))


# REMOVE SUBSCRIPTION

@app.route("/remove", methods=["POST"])
def remove():
    if "email" not in session:
        return redirect(url_for("login"))

    sub_table = dynamodb.Table(SUBSCRIPTIONS_TABLE)

    sub_table.delete_item(
        Key={
            "email": session["email"],
            "song_id": request.form["song_id"]
        }
    )

    return redirect(url_for("main"))


# LOGOUT

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)