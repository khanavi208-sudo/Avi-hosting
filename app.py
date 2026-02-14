from flask import Flask, render_template, request, redirect, session, jsonify
import os, json, subprocess, time, signal

app = Flask(__name__)
app.secret_key = "supersecret"

UPLOAD = "uploads"
os.makedirs(UPLOAD, exist_ok=True)

BOT_PROCESS = None
START_TIME = None

def access_key():
    return open("access_key.txt").read().strip()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    if request.form["key"] == access_key():
        session["user"] = True
        return redirect("/dashboard")
    return "Wrong access key"

@app.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect("/")
    return render_template("dashboard.html")

@app.route("/upload", methods=["POST"])
def upload():
    f = request.files["file"]
    if not f.filename.endswith(".py"):
        return jsonify({"error": "Only Python files allowed"})
    path = os.path.join(UPLOAD, f.filename)
    f.save(path)

    return jsonify({
        "name": f.filename,
        "size": os.path.getsize(path),
        "edited": time.ctime(os.path.getmtime(path))
    })

@app.route("/run", methods=["POST"])
def run():
    global BOT_PROCESS, START_TIME
    file = request.json["file"]
    path = os.path.join(UPLOAD, file)

    if BOT_PROCESS:
        return jsonify({"status": "already running"})

    BOT_PROCESS = subprocess.Popen(["python", path])
    START_TIME = time.ctime()
    return jsonify({
        "webhook": "successfully",
        "running": True,
        "start": START_TIME
    })

@app.route("/stop", methods=["POST"])
def stop():
    global BOT_PROCESS
    if BOT_PROCESS:
        BOT_PROCESS.terminate()
        BOT_PROCESS = None
        return jsonify({"stopped": True})
    return jsonify({"stopped": False})

@app.route("/status")
def status():
    return jsonify({
        "running": BOT_PROCESS is not None,
        "start": START_TIME
    })

@app.route("/admin", methods=["GET","POST"])
def admin():
    data = json.load(open("admin.json"))
    if request.method == "POST":
        if request.form["email"] == data["email"] and request.form["password"] == data["password"]:
            session["admin"] = True
            return redirect("/panel")
        return "Admin login failed"
    return render_template("admin.html")

@app.route("/panel", methods=["GET","POST"])
def panel():
    if not session.get("admin"):
        return redirect("/admin")
    if request.method == "POST":
        open("access_key.txt","w").write(request.form["newkey"])
    return f"""
    <h2>Admin Panel</h2>
    Current key: {access_key()}
    <form method=post>
    <input name=newkey placeholder="New Access Key">
    <button>Change</button>
    </form>
    """

app.run(host="0.0.0.0", port=10000)
