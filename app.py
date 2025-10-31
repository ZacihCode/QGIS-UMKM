from flask import Flask, render_template, request, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
import csv
from datetime import datetime
import pymysql

# === Load environment variables ===
load_dotenv()

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

# === Build DATABASE_URL from .env values ===
db_host = os.getenv("DATABASE_HOST")
db_user = os.getenv("DATABASE_USER")
db_pass = os.getenv("DATABASE_PASSWORD")
db_name = os.getenv("DATABASE_NAME")

# Encode karakter khusus di password (contoh: !, @, %, dll)
from urllib.parse import quote_plus

db_pass_encoded = quote_plus(db_pass)

DATABASE_URL = f"mysql+pymysql://{db_user}:{db_pass_encoded}@{db_host}:3306/{db_name}?charset=utf8mb4"

# === SQLAlchemy Config ===
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
try:
    conn = pymysql.connect(
        host=db_host, user=db_user, password=db_pass, database=db_name
    )
    print("✅ Database connected OK!")
    conn.close()
except Exception as e:
    print("❌ DB connection error:", e)
db = SQLAlchemy(app)


# ===========================
# 📄 Model Table UMKM
# ===========================
class UMKMData(db.Model):
    __tablename__ = "umkm_data"
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.String(50))
    longitude = db.Column(db.String(50))
    nama = db.Column(db.String(255))
    nim = db.Column(db.String(100))
    kelas = db.Column(db.String(100))
    umkm = db.Column(db.String(255))
    kategori = db.Column(db.String(100))
    pegawai = db.Column(db.String(50))
    foto = db.Column(db.String(255))


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

    new_data = UMKMData(
        latitude=latitude,
        longitude=longitude,
        nama=nama,
        nim=nim,
        kelas=kelas,
        umkm=umkm,
        kategori=kategori,
        pegawai=pegawai,
        foto=filename,
    )
    db.session.add(new_data)
    db.session.commit()

    return redirect(url_for("data"))


# ===========================
# 📊 Tampilkan Data
# ===========================
@app.route("/data")
def data():
    records = UMKMData.query.order_by(UMKMData.id.desc()).all()
    return render_template("data.html", data=records)


# ===========================
# 📦 Export ke CSV
# ===========================
@app.route("/export")
def export():
    records = UMKMData.query.all()
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
                    r.id,
                    r.latitude,
                    r.longitude,
                    r.nama,
                    r.nim,
                    r.kelas,
                    r.umkm,
                    r.kategori,
                    r.pegawai,
                    r.foto,
                ]
            )

    return send_file(csv_path, as_attachment=True)


# ===========================
# ✏️ Edit Data
# ===========================
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    record = UMKMData.query.get_or_404(id)

    if request.method == "POST":
        record.nama = request.form["nama"]
        record.nim = request.form["nim"]
        record.kelas = request.form["kelas"]
        record.umkm = request.form["umkm"]
        record.kategori = request.form["kategori"]
        record.pegawai = request.form["pegawai"]

        foto = request.files.get("foto")
        if foto and foto.filename != "":
            old_path = os.path.join(app.config["UPLOAD_FOLDER"], record.foto)
            if os.path.exists(old_path):
                os.remove(old_path)

            filename = datetime.now().strftime("%Y%m%d_%H%M%S_") + secure_filename(
                foto.filename
            )
            foto_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            foto.save(foto_path)
            record.foto = filename

        db.session.commit()
        return redirect(url_for("data"))

    return render_template("edit.html", data=record)


# ===========================
# 🗑️ Hapus Data
# ===========================
@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    record = UMKMData.query.get_or_404(id)
    if record.foto:
        try:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], record.foto))
        except FileNotFoundError:
            pass

    db.session.delete(record)
    db.session.commit()
    return redirect(url_for("data"))


# ===========================
# 🚀 Jalankan
# ===========================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
