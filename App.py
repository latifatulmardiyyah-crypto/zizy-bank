from flask import Flask, request, jsonify, render_template, session
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "zizy-rahasia-2025")

# Data nasabah (di produksi pakai database)
nasabah = {
    "evan": {"password": "evan123", "pin": "1111", "rekening": "151001",
             "saldo": 5000000, "bank": "002", "nama": "Evan"},
    "sean": {"password": "sean123", "pin": "2222", "rekening": "140209",
             "saldo": 3000000, "bank": "001", "nama": "Sean"},
    "ziva": {"password": "ziva123", "pin": "3333", "rekening": "110706",
             "saldo": 10000000, "bank": "001", "nama": "Ziva"},
}

def cari_user_by_rekening(rek):
    for nama, d in nasabah.items():
        if d["rekening"] == rek:
            return nama, d
    return None, None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/login", methods=["POST"])
def login():
    d = request.json or {}
    u, p = d.get("username", "").strip().lower(), d.get("password", "")
    if u in nasabah and nasabah[u]["password"] == p:
        session["user"] = u
        return jsonify({"ok": True, "nama": nasabah[u]["nama"]})
    return jsonify({"ok": False, "msg": "Username atau password salah"}), 401

@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"ok": True})

def current_user():
    u = session.get("user")
    return u, nasabah.get(u)

@app.route("/api/saldo", methods=["POST"])
def saldo():
    u, data = current_user()
    if not u:
        return jsonify({"ok": False, "msg": "Belum login"}), 401
    d = request.json or {}
    if d.get("pin") != data["pin"]:
        return jsonify({"ok": False, "msg": "PIN salah"}), 401
    return jsonify({"ok": True, "saldo": data["saldo"]})

@app.route("/api/tarik", methods=["POST"])
def tarik():
    u, data = current_user()
    if not u:
        return jsonify({"ok": False, "msg": "Belum login"}), 401
    d = request.json or {}
    if d.get("pin") != data["pin"]:
        return jsonify({"ok": False, "msg": "PIN salah"}), 401
    try:
        jumlah = int(d.get("jumlah", 0))
    except (ValueError, TypeError):
        return jsonify({"ok": False, "msg": "Jumlah tidak valid"}), 400
    if jumlah <= 0:
        return jsonify({"ok": False, "msg": "Jumlah harus > 0"}), 400
    if jumlah > data["saldo"]:
        return jsonify({"ok": False, "msg": "Saldo tidak cukup"}), 400
    data["saldo"] -= jumlah
    return jsonify({"ok": True, "saldo": data["saldo"], "jumlah": jumlah})

@app.route("/api/transfer", methods=["POST"])
def transfer():
    u, data = current_user()
    if not u:
        return jsonify({"ok": False, "msg": "Belum login"}), 401
    d = request.json or {}
    if d.get("pin") != data["pin"]:
        return jsonify({"ok": False, "msg": "PIN salah"}), 401
    rek = d.get("rekening", "")
    kode = d.get("kode_bank", "")
    try:
        jumlah = int(d.get("jumlah", 0))
    except (ValueError, TypeError):
        return jsonify({"ok": False, "msg": "Jumlah tidak valid"}), 400

    nama_tujuan, tujuan = cari_user_by_rekening(rek)
    if not tujuan:
        return jsonify({"ok": False, "msg": "Rekening tujuan tidak ditemukan"}), 404
    if kode != tujuan["bank"]:
        return jsonify({"ok": False, "msg": "Kode bank salah"}), 400

    admin = 0 if data["bank"] == tujuan["bank"] else 6500
    total = jumlah + admin
    if total > data["saldo"]:
        return jsonify({"ok": False, "msg": "Saldo tidak cukup"}), 400

    data["saldo"] -= total
    tujuan["saldo"] += jumlah
    return jsonify({
        "ok": True, "saldo": data["saldo"], "jumlah": jumlah,
        "admin": admin, "total": total, "penerima": tujuan["nama"]
    })

if __name__ == "__main__":
    app.run(debug=True)