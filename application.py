import os
import json
import logging
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
DATA_PATH = os.path.join(BASE_DIR, "photos.json")
LOG_PATH = os.path.join(BASE_DIR, "photoportal.log")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---- Logging (spec mentions photoportal.log) ----
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ---- tiny persistence layer ----
def load_photos():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_photos(items):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)

def current_user_type():
    # Assumption (spec): admin username will NOT be a gmail; general users end with @gmail.com
    # We rely on that to decide where logout should go. 
    u = session.get("user")
    if not u:
        return None
    return "general" if u.endswith("@gmail.com") else "admin"

# ---- General user login page (1.1, 1.2) ----
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")  # one email input (gmail)

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip()
    # Spec: no need to verify gmail; assume xyz@gmail.com format will be used. 
    session["user"] = email
    logger.info("General user logged in: %s", email)
    return redirect(url_for("portal"))

# ---- Admin login page (no verification required per assumptions) (1 admin) ----
@app.route("/admin", methods=["GET"])
def admin_index():
    return render_template("adminindex.html")  # username + password form

@app.route("/admin/login", methods=["POST"])
def admin_login():
    username = request.form.get("username", "").strip()
    # Spec says: we won't verify correctness of username/password for this assignment. 
    session["user"] = username
    logger.info("Admin logged in: %s", username)
    return redirect(url_for("portal"))

# ---- Landing page for both user types (1.3, 1.4) ----
@app.route("/portal", methods=["GET"])
def portal():
    user = session.get("user")
    if not user:
        return redirect(url_for("index"))
    photos = load_photos()
    # Upload form shown only for admin (spec). Landing page shows blue side panes already. 
    return render_template(
        "photo-portal.html",
        user=user,
        is_admin=current_user_type() == "admin",
        photos=photos,
        status_msg="TODO: Implement slide-show functionality"  # (1.3.1) 
    )

# ---- Upload (admin only). Store photo + metadata (date, tags) (3.1) ----
@app.route("/upload", methods=["POST"])
def upload():
    if current_user_type() != "admin":
        return redirect(url_for("portal"))
    f = request.files.get("photo_name")
    date_taken = request.form.get("date_taken", "").strip()
    tags = request.form.get("tags", "").strip()

    if not f or f.filename == "":
        flash("No file provided")
        return redirect(url_for("portal"))

    filename = f.filename
    # Spec assumption 2: we can assume only images are used in testing; no need to enforce type. 
    f.save(os.path.join(UPLOAD_DIR, filename))

    items = load_photos()
    # overwrite if same name:
    items = [p for p in items if p["name"] != filename]
    items.append({
        "name": filename,
        "url": f"/static/uploads/{filename}",
        "date_taken": date_taken,
        "tags": tags
    })
    save_photos(items)
    logger.info("Uploaded %s (date=%s, tags=%s)", filename, date_taken, tags)

    # 3.1 status message: "Photo <photo-file-name> uploaded successfully." 
    return render_template(
        "photo-portal.html",
        user=session.get("user"),
        is_admin=True,
        photos=load_photos(),
        status_msg=f"Photo {filename} uploaded successfully."
    )

# ---- Search (5.1, 5.3-5.5) ----
@app.route("/search", methods=["POST"])
def search():
    user = session.get("user")
    if not user:
        return redirect(url_for("index"))

    by = request.form.get("searchBy", "")
    text = request.form.get("searchText", "").strip()
    date = request.form.get("searchDate", "").strip()
    tags = request.form.get("searchTags", "").strip()

    items = load_photos()
    matched = []

    def matches_tags(photo_tags, q):
        # compare if ANY tag matches (case-insensitive)
        pt = [t.strip().lower() for t in (photo_tags or "").split(",") if t.strip()]
        qt = [t.strip().lower() for t in (q or "").split(",") if t.strip()]
        return any(t in pt for t in qt) if qt else False

    for p in items:
        if by == "name":
            if text and text.lower() in p["name"].lower():
                matched.append(p)
        elif by == "date":
            # exact match required for date (5.3) 
            if date and date == p.get("date_taken", ""):
                matched.append(p)
        elif by == "tags":
            if tags and matches_tags(p.get("tags", ""), tags):
                matched.append(p)

    if matched:
        status = "Matching photos found"  # (5.4.1) 
    else:
        status = "No matching photos found"  # (5.5.1) 

    return render_template(
        "photo-portal.html",
        user=user,
        is_admin=current_user_type() == "admin",
        photos=matched,
        status_msg=status
    )

# ---- Logout (2.1, 2.2) ----
@app.route("/logout", methods=["GET"])
def logout():
    user = session.get("user")
    session.clear()
    # Redirect based on user type (admin -> /admin, general -> /) 
    if user and user.endswith("@gmail.com"):
        return redirect(url_for("index"))
    else:
        return redirect(url_for("admin_index"))

# Static helper (not strictly needed; Flask serves /static)
@app.route("/static/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5009, debug=True)
