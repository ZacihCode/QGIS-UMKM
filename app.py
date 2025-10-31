from flask import Flask, render_template, request, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import csv
import requests
from datetime import datetime

# === Load environment ===
load_dotenv()

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

# === API Base URL ===
API_BASE = "https://pilihin.my.id/api/umkm"
API_KEY = os.getenv("API_KEY", "kodiva123")  # optional keamanan

HEADERS = {"X-API-KEY": API_KEY, "Accept": "application/json"}


# ===========================
# 📄 Form Input
# ===========================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")
    nama = request.form["nama"]
    nim = request.form["nim"]
    kelas = request.form["kelas"]
    umkm = request.form["umkm"]
    kategori = request.form["kategori"]
    pegawai = request.form["pegawai"]

    foto = request.files["foto"]
    filename = datetime.now().strftime("%Y%m%d_%H%M%S_") + secure_filename(
        foto.filename
    )
    foto_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    foto.save(foto_path)

    # Kirim ke Laravel API
    with open(foto_path, "rb") as f:
        files = {"foto": f}
        data = {
            "latitude": latitude,
            "longitude": longitude,
            "nama": nama,
            "nim": nim,
            "kelas": kelas,
            "umkm": umkm,
            "kategori": kategori,
            "pegawai": pegawai,
        }
        res = requests.post(API_BASE, data=data, files=files, headers=HEADERS)

    os.remove(foto_path)

    if res.status_code == 201:
        return redirect(url_for("data"))
    else:
        return f"<pre>Error: {res.status_code}\n{res.text}</pre>", 400


# ===========================
# 📊 Tampilkan Data
# ===========================
@app.route("/data")
def data():
    res = requests.get(API_BASE, headers=HEADERS)
    if res.status_code != 200:
        return f"<pre>Gagal ambil data API\n{res.text}</pre>", 500
    records = res.json()
    return render_template("data.html", data=records)


# ===========================
# 📦 Export ke CSV
# ===========================
@app.route("/export")
def export():
    res = requests.get(API_BASE, headers=HEADERS)
    if res.status_code != 200:
        return f"<pre>Gagal export data\n{res.text}</pre>", 500

    records = res.json()
    filename = "data_umkm.csv"
    csv_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "ID",
                "Latitude",
                "Longitude",
                "Nama",
                "NIM",
                "Kelas",
                "UMKM",
                "Kategori",
                "Pegawai",
                "Foto",
            ]
        )
        for r in records:
            writer.writerow(
                [
                    r.get("id"),
                    r.get("latitude"),
                    r.get("longitude"),
                    r.get("nama"),
                    r.get("nim"),
                    r.get("kelas"),
                    r.get("umkm"),
                    r.get("kategori"),
                    r.get("pegawai"),
                    r.get("foto"),
                ]
            )

    return send_file(csv_path, as_attachment=True)


# ===========================
# ✏️ Edit Data
# ===========================
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    # Ambil data dulu
    record = requests.get(f"{API_BASE}/{id}", headers=HEADERS).json()

    if request.method == "POST":
        data = {
            "nama": request.form["nama"],
            "nim": request.form["nim"],
            "kelas": request.form["kelas"],
            "umkm": request.form["umkm"],
            "kategori": request.form["kategori"],
            "pegawai": request.form["pegawai"],
        }

        foto = request.files.get("foto")
        files = None
        if foto and foto.filename != "":
            filename = datetime.now().strftime("%Y%m%d_%H%M%S_") + secure_filename(
                foto.filename
            )
            foto_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            foto.save(foto_path)
            files = {"foto": open(foto_path, "rb")}

        res = requests.post(
            f"{API_BASE}/{id}/update", data=data, files=files, headers=HEADERS
        )

        if files:
            files["foto"].close()
            os.remove(foto_path)

        if res.status_code == 200:
            return redirect(url_for("data"))
        else:
            return f"<pre>Error: {res.status_code}\n{res.text}</pre>", 400

    return render_template("edit.html", data=record)


# ===========================
# 🗑️ Hapus Data
# ===========================
@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    res = requests.delete(f"{API_BASE}/{id}", headers=HEADERS)
    if res.status_code == 200:
        return redirect(url_for("data"))
    else:
        return f"<pre>Gagal hapus data: {res.text}</pre>", 400


@app.errorhandler(Exception)
def handle_error(e):
    import traceback

    traceback.print_exc()
    return f"<pre>{traceback.format_exc()}</pre>", 500


# ===========================
# 🚀 Jalankan
# ===========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
