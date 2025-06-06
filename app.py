from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import os
import sys

app = Flask(__name__)

BASE_URL = "https://foro.squadalpha.es"
LOGIN_URL = f"{BASE_URL}/ucp.php?mode=login"
FORUM_URL = f"{BASE_URL}/viewforum.php?f=18"

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

def login_to_forum(session):
    login_page = session.get(LOGIN_URL)
    soup = BeautifulSoup(login_page.text, "html.parser")

    form_token = soup.find("input", {"name": "form_token"})["value"]
    creation_time = soup.find("input", {"name": "creation_time"})["value"]

    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "login": "Login",
        "autologin": "on",
        "redirect": "index.php",
        "creation_time": creation_time,
        "form_token": form_token
    }

    session.post(LOGIN_URL, data=payload)

def get_bbcode_posts():
    session = requests.Session()

    # Simular navegador real
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    })

    login_to_forum(session)

    forum_page = session.get(FORUM_URL)
    soup = BeautifulSoup(forum_page.text, "html.parser")

    topic_links = soup.select(".topictitle")[:3]
    posts_bbcode = []

    for link in topic_links:
        href = link["href"]
        post_url = BASE_URL + href.replace("&amp;", "&")
        print(f"Accediendo a: {post_url}", file=sys.stdout, flush=True)

        post_page = session.get(post_url)
        post_soup = BeautifulSoup(post_page.text, "html.parser")

        quote_link = post_soup.find("a", href=lambda x: x and "mode=quote" in x)
        if not quote_link:
            print("No se encontró botón de citar.", file=sys.stdout, flush=True)
            continue

        quote_url = BASE_URL + "/" + quote_link["href"].replace("&amp;", "&")
        print(f"Cargando BBCode desde: {quote_url}", file=sys.stdout, flush=True)

        quote_page = session.get(quote_url)

        # DEBUG extra
        print("URL cargada:", quote_page.url, file=sys.stdout, flush=True)
        print("Longitud del HTML:", len(quote_page.text), file=sys.stdout, flush=True)

        if "No estás autorizado" in quote_page.text or "login" in quote_page.url:
            print("¡El foro dice que no hay permisos!", file=sys.stdout, flush=True)

        quote_soup = BeautifulSoup(quote_page.text, "html.parser")
        textarea = quote_soup.find("textarea", {"name": "message"})

        if textarea:
            print("BBCode encontrado.", file=sys.stdout, flush=True)
            posts_bbcode.append(textarea.text.strip())
        else:
            print("No se encontró textarea con BBCode.", file=sys.stdout, flush=True)

    return posts_bbcode

@app.route("/api/posts")
def api_posts():
    try:
        posts = get_bbcode_posts()
        return jsonify({"posts": posts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
