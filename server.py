import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from datetime import timedelta

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, session, url_for, Response
from markupsafe import escape

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__, static_folder="build/")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(seconds=10)
app.secret_key = env.get("APP_SECRET_KEY")

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)


def login():
    print(f"forwarding user to login.")
    print(str(url_for("home", _external=True, subpath="callback")))
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("home", _external=True, subpath="callback")
    )


def callback(subpath):
    token = oauth.auth0.authorize_access_token()
    print(f"setting session user token")
    session.permanent = True
    session["user"] = token
    if subpath == "callback" and session.get("callback_url"):
        # occurs after PERMANENT_SESSION_LIFETIME timeout
        subpath = session.get("callback_url")
    return load_html(subpath)


def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True, subpath="login"),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


def load_html(subpath):
    if subpath == "callback":
        # occurs on first login
        subpath = "intro.html"
    return app.send_static_file(subpath)


@app.route("/")
@app.route("/<path:subpath>", methods=["GET", "POST"])
def home(subpath="index.html"):

    if subpath == "logout":
        print(f"logout")
        return logout()
    elif session.get("user"):
        return load_html(subpath)
    else:
        try:
            return callback(subpath)
        except Exception as e:
            session["callback_url"] = subpath
            return login()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 5000), debug=True)
