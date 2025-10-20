from flask import Flask, render_template, url_for, jsonify, request
import pathlib
import json

app = Flask(__name__)

# Data alat — hanya metadata & perintah sebagai teks (TIDAK dieksekusi)
TOOLS = [
    {
        "id": "hammer",
        "name": "Hammer",
        "desc": "HTTP DoS tool (repo). Tampilkan perintah instalasi untuk referensi.",
        "repo": "https://github.com/cyweb/hammer",
        "install_cmds": [
            "pkg update && pkg upgrade",
            "pkg install python",
            "pkg install git",
            "git clone https://github.com/cyweb/hammer"
        ]
    },
    {
        "id": "spammer-grab",
        "name": "Spammer-Grab",
        "desc": "Spammer-Grab repo (referensi).",
        "repo": "https://github.com/p4kl0nc4t/Spammer-Grab",
        "install_cmds": [
            "pkg update && pkg upgrade",
            "pkg install git",
            "pkg install python",
            "git clone https://github.com/p4kl0nc4t/Spammer-Grab"
        ]
    },
    {
        "id": "red-hawk",
        "name": "RED_HAWK",
        "desc": "Reconnaissance tool (repo).",
        "repo": "https://github.com/Tuhinshubhra/RED_HAWK",
        "install_cmds": [
            "apt update && apt upgrade",
            "apt install php",
            "apt install git",
            "git clone https://github.com/Tuhinshubhra/RED_HAWK"
        ]
    },
    {
        "id": "infoga",
        "name": "Infoga",
        "desc": "Gathering e-mail information (repo).",
        "repo": "https://github.com/m4ll0k/Infoga",
        "install_cmds": [
            "apt update && apt upgrade",
            "apt install git",
            "pkg install python2",
            "git clone https://github.com/m4ll0k/Infoga.git infoga",
            "cd infoga && pip install -r requirements.txt"
        ]
    },
    {
        "id": "d-tect",
        "name": "D-TECT",
        "desc": "Multi-tool reconnaissance (repo).",
        "repo": "https://github.com/shawarkhanethicalhacker/D-TECT",
        "install_cmds": [
            "apt update && apt upgrade",
            "apt-get install python",
            "apt-get install git",
            "git clone https://github.com/shawarkhanethicalhacker/D-TECT"
        ]
    },
    # Tambahkan metadata tool lain jika perlu — hanya untuk dokumentasi
]

@app.route("/")
def index():
    return render_template("index.html", tools=TOOLS)

@app.route("/tool/<tool_id>")
def tool_detail(tool_id):
    tool = next((t for t in TOOLS if t["id"] == tool_id), None)
    if not tool:
        return ("Tool not found", 404)
    return render_template("tool.html", tool=tool)

# API endpoint read-only (useful jika mau integrasi front-end)
@app.route("/api/tools")
def api_tools():
    return jsonify(TOOLS)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
