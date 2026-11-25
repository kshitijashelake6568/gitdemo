from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)

DATABASE = "seminar.db"


# Database connection
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Create database table
def create_table():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            hall TEXT NOT NULL,
            day TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            event TEXT,
            dept TEXT,
            role TEXT,
            status TEXT DEFAULT 'Active'
        )
    """)

    conn.commit()
    conn.close()


# User page
@app.route("/")
def home():
    return render_template("user.html")


# Admin page
@app.route("/admin")
def admin():
    return render_template("admin.html")


# Department page
@app.route("/department")
def department():
    return render_template("department.html")


# Get bookings
@app.route("/api/bookings", methods=["GET"])
def get_bookings():
    conn = get_db()

    hall = request.args.get("hall")
    date = request.args.get("date")

    query = "SELECT * FROM bookings WHERE 1=1"
    values = []

    if hall:
        query += " AND hall=?"
        values.append(hall)

    if date:
        query += " AND date=?"
        values.append(date)

    result = conn.execute(query, values).fetchall()
    conn.close()

    return jsonify([dict(row) for row in result])


# Add booking
@app.route("/api/bookings", methods=["POST"])
def add_booking():
    data = request.get_json(silent=True) or {}

    required = [
        "username", "hall", "date", "time",
        "event", "dept", "role"
    ]

    for field in required:
        if not data.get(field):
            return jsonify({"error": field + " is required"}), 400

    conn = get_db()

    existing = conn.execute("""
        SELECT id FROM bookings
        WHERE hall=? AND date=? AND time=?
        AND status='Active'
    """, (data["hall"], data["date"], data["time"])).fetchone()

    if existing:
        conn.close()
        return jsonify({"error": "This hall is already booked"}), 409

    conn.execute("""
        INSERT INTO bookings
        (username, hall, day, date, time, event, dept, role)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["username"],
        data["hall"],
        data.get("day", ""),
        data["date"],
        data["time"],
        data["event"],
        data["dept"],
        data["role"]
    ))

    conn.commit()
    conn.close()

    return jsonify({"message": "Booking successful"}), 201


# Get user bookings
@app.route("/api/bookings/user/<username>", methods=["GET"])
def get_user_bookings(username):
    conn = get_db()

    result = conn.execute("""
        SELECT * FROM bookings WHERE username=?
    """, (username,)).fetchall()

    conn.close()

    return jsonify([dict(row) for row in result])


# Cancel user bookings for a hall
@app.route("/api/bookings/user/<username>/hall/<path:hall>",
           methods=["DELETE"])
def cancel_user_bookings(username, hall):
    conn = get_db()

    conn.execute("""
        DELETE FROM bookings
        WHERE username=? AND hall=?
    """, (username, hall))

    conn.commit()
    conn.close()

    return jsonify({"message": "Booking removed successfully"})


# Delete selected bookings
@app.route("/api/bookings", methods=["DELETE"])
def delete_bookings():
    data = request.get_json(silent=True) or {}
    ids = data.get("ids", [])

    if not ids:
        return jsonify({"error": "No bookings selected"}), 400

    conn = get_db()

    placeholders = ",".join("?" for _ in ids)

    conn.execute(
        f"DELETE FROM bookings WHERE id IN ({placeholders})",
        ids
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Bookings deleted successfully"})


# Run application
if __name__ == "__main__":
    create_table()
    app.run(debug=True)