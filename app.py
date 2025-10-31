from flask import Flask, render_template, request, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import os
import csv
import pymysql
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db = pymysql.connect(
    host=os.getenv("DATABASE_HOST"),
    user=os.getenv("DATABASE_USER"),
    password=os.getenv("DATABASE_PASSWORD"),
    database=os.getenv("DATABASE_NAME"),
    cursorclass=pymysql.cursors.DictCursor,
)


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

    cursor = db.cursor()
    sql = """
        INSERT INTO umkm_data (latitude, longitude, nama, nim, kelas, umkm, kategori, pegawai, foto)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    cursor.execute(
        sql, (latitude, longitude, nama, nim, kelas, umkm, kategori, pegawai, filename)
    )
    db.commit()
    cursor.close()

    return redirect(url_for("data"))


# ===========================
# 📊 Tampilkan Data
# ===========================
@app.route("/data")
def data():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM umkm_data ORDER BY id DESC")
    records = cursor.fetchall()
    cursor.close()
    return render_template("data.html", data=records)


# ===========================
# 📦 Export ke CSV
# ===========================
@app.route("/export")
def export():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM umkm_data")
    records = cursor.fetchall()
    cursor.close()

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
                    r["id"],
                    r["latitude"],
                    r["longitude"],
                    r["nama"],
                    r["nim"],
                    r["kelas"],
                    r["umkm"],
                    r["kategori"],
                    r["pegawai"],
                    r["foto"],
                ]
            )

    return send_file(csv_path, as_attachment=True)


# ===========================
# ✏️ Edit Data
# ===========================
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    cursor = db.cursor()

    # Ambil data lama
    cursor.execute("SELECT * FROM umkm_data WHERE id=%s", (id,))
    record = cursor.fetchone()

    if not record:
        cursor.close()
        return "Data tidak ditemukan", 404

    if request.method == "POST":
        nama = request.form["nama"]
        nim = request.form["nim"]
        kelas = request.form["kelas"]
        umkm = request.form["umkm"]
        kategori = request.form["kategori"]
        pegawai = request.form["pegawai"]

        # Cek apakah ada foto baru
        foto = request.files.get("foto")
        filename = record["foto"]  # default pakai foto lama

        if foto and foto.filename != "":
            # Hapus foto lama (jika ada)
            old_path = os.path.join(app.config["UPLOAD_FOLDER"], record["foto"])
            if os.path.exists(old_path):
                os.remove(old_path)

            # Simpan foto baru
            filename = datetime.now().strftime("%Y%m%d_%H%M%S_") + secure_filename(
                foto.filename
            )
            foto_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            foto.save(foto_path)

        # Update data
        sql = """UPDATE umkm_data 
                 SET nama=%s, nim=%s, kelas=%s, umkm=%s, kategori=%s, pegawai=%s, foto=%s 
                 WHERE id=%s"""
        cursor.execute(sql, (nama, nim, kelas, umkm, kategori, pegawai, filename, id))
        db.commit()
        cursor.close()

        return redirect(url_for("data"))

    cursor.close()
    return render_template("edit.html", data=record)


# ===========================
# 🗑️ Hapus Data
# ===========================
@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    cursor = db.cursor()
    cursor.execute("SELECT foto FROM umkm_data WHERE id=%s", (id,))
    record = cursor.fetchone()
    if record and record["foto"]:
        try:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], record["foto"]))
        except FileNotFoundError:
            pass

    cursor.execute("DELETE FROM umkm_data WHERE id=%s", (id,))
    db.commit()
    cursor.close()
    return redirect(url_for("data"))


if __name__ == "__main__":
    app.run(debug=True)
