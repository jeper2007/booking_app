from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3, random, string, threading, webbrowser, re, os

app = Flask(__name__)
app.secret_key = "luxstay_secret_2024"

# ── DATABASE ───────────────────────────────────────────────────────────────────
# Vercel has a read-only filesystem. We must use /tmp for the database if on Vercel.
IF_VERCEL = os.environ.get("VERCEL")
if IF_VERCEL:
    DB_PATH = "/tmp/database.db"
    # Seed the DB from the repo to /tmp if it doesn't exist yet
    if not os.path.exists(DB_PATH):
        import shutil
        SOURCE_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")
        if os.path.exists(SOURCE_DB):
            shutil.copy(SOURCE_DB, DB_PATH)
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")

def get_db():
    # Ensure directory exists (mostly for local development if DB_PATH was changed)
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        name TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS bookings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        hotel TEXT,
        location TEXT,
        check_in TEXT,
        check_out TEXT,
        guests INTEGER,
        room_type TEXT,
        price TEXT,
        ref_code TEXT,
        status TEXT DEFAULT 'pending',
        price_value REAL DEFAULT 0)""")

    # Migrate existing DB — add new columns if missing
    for col, definition in [("status", "TEXT DEFAULT 'pending'"), ("price_value", "REAL DEFAULT 0")]:
        try:
            c.execute(f"ALTER TABLE bookings ADD COLUMN {col} {definition}")
        except Exception:
            pass
    c.execute("""CREATE TABLE IF NOT EXISTS admins(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        name TEXT)""")
    # Seed default admin if none exists
    c.execute("SELECT COUNT(*) FROM admins")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO admins(email,password,name) VALUES(?,?,?)",
                  ("admin@luxstay.ph", "admin123", "LuxStay Admin"))
    conn.commit()
    conn.close()

init_db()

# ── HOTEL DATA ────────────────────────────────────────────────────────────────
hotels_data = [
    {
        "name": "Hotel Manila Bay",
        "location": "Manila",
        "image": "manila.jpg",
        "price": "₱4,500",
        "rating": 4.8,
        "type": "City",
        "description": "Experience the vibrant heart of Metro Manila with breathtaking bay views, world-class dining, and modern amenities.",
        "amenities": ["Free WiFi", "Pool", "Spa", "Gym", "Restaurant", "Bar"],
        "rooms": [
            {"type": "Deluxe Room",    "price": "₱4,500/night",  "desc": "City view, King bed, 35 sqm"},
            {"type": "Superior Suite", "price": "₱7,200/night",  "desc": "Bay view, King bed, 55 sqm"},
            {"type": "Executive Suite","price": "₱12,000/night", "desc": "Panoramic view, 2 beds, 80 sqm"},
        ],
        "gallery": ["manila.jpg","cebu.jpg","davao.jpg","boracay.jpg"]
    },
    {
        "name": "Cebu Island Resort",
        "location": "Cebu",
        "image": "cebu.jpg",
        "price": "₱6,800",
        "rating": 4.9,
        "type": "Beach",
        "description": "A tropical paradise on the shores of Cebu, offering pristine white sands, coral reefs, and luxurious island living.",
        "amenities": ["Private Beach","Snorkeling","Free WiFi","Pool","Spa","Water Sports"],
        "rooms": [
            {"type": "Garden Room",    "price": "₱6,800/night",  "desc": "Garden view, Queen bed, 30 sqm"},
            {"type": "Beach Villa",    "price": "₱11,500/night", "desc": "Beachfront, King bed, 60 sqm"},
            {"type": "Ocean Bungalow", "price": "₱18,000/night", "desc": "Overwater, King bed, 70 sqm"},
        ],
        "gallery": ["cebu.jpg","boracay.jpg","manila.jpg","davao.jpg"]
    },
    {
        "name": "Davao Garden Inn",
        "location": "Davao",
        "image": "davao.jpg",
        "price": "₱3,200",
        "rating": 4.5,
        "type": "City",
        "description": "Nestled at the foot of Mount Apo, Davao Garden Inn offers a serene escape with lush tropical gardens and Filipino hospitality.",
        "amenities": ["Free WiFi","Garden","Restaurant","Gym","Meeting Rooms"],
        "rooms": [
            {"type": "Standard Room", "price": "₱3,200/night", "desc": "Garden view, Double bed, 25 sqm"},
            {"type": "Deluxe Room",   "price": "₱5,000/night", "desc": "Mountain view, King bed, 38 sqm"},
            {"type": "Family Suite",  "price": "₱8,500/night", "desc": "Full suite, 2 beds, 65 sqm"},
        ],
        "gallery": ["davao.jpg","baguio.jpg","manila.jpg","cebu.jpg"]
    },
    {
        "name": "Boracay Pearl Resort",
        "location": "Boracay",
        "image": "boracay.jpg",
        "price": "₱9,500",
        "rating": 4.9,
        "type": "Beach",
        "description": "Set on the world-famous White Beach of Boracay, Pearl Resort epitomizes tropical luxury with sunset views and crystal-clear waters.",
        "amenities": ["Beachfront","Infinity Pool","Free WiFi","Spa","Water Sports","Nightclub"],
        "rooms": [
            {"type": "Beach Room",    "price": "₱9,500/night",  "desc": "Sea view, Queen bed, 35 sqm"},
            {"type": "Premium Suite", "price": "₱16,000/night", "desc": "Beachfront, King bed, 65 sqm"},
            {"type": "Villa",         "price": "₱25,000/night", "desc": "Private pool villa, King bed, 100 sqm"},
        ],
        "gallery": ["boracay.jpg","cebu.jpg","manila.jpg","davao.jpg"]
    },
    {
        "name": "Baguio Pine Lodge",
        "location": "Baguio",
        "image": "baguio.jpg",
        "price": "₱3,800",
        "rating": 4.6,
        "type": "Mountain",
        "description": "Escape the heat in Baguio's cool mountain embrace. Pine Lodge offers cozy rooms amid towering pine trees and cool highland air.",
        "amenities": ["Fireplace","Mountain View","Free WiFi","Restaurant","Garden"],
        "rooms": [
            {"type": "Cozy Room",    "price": "₱3,800/night", "desc": "Forest view, Queen bed, 28 sqm"},
            {"type": "Superior Room","price": "₱5,500/night", "desc": "Mountain view, King bed, 40 sqm"},
            {"type": "Chalet Suite", "price": "₱9,000/night", "desc": "Private deck, 2 beds, 70 sqm"},
        ],
        "gallery": ["baguio.jpg","davao.jpg","manila.jpg","cebu.jpg"]
    },
    {
        "name": "Palawan Horizon Hotel",
        "location": "Palawan",
        "image": "boracay.jpg",
        "price": "₱11,200",
        "rating": 5.0,
        "type": "Beach",
        "description": "In the last frontier of the Philippines, Horizon Hotel offers unmatched natural beauty, world-class diving, and eco-luxury stays.",
        "amenities": ["Diving Center","Kayaking","Eco Pool","Restaurant","Free WiFi","Spa"],
        "rooms": [
            {"type": "Nature Room",  "price": "₱11,200/night", "desc": "Jungle view, King bed, 40 sqm"},
            {"type": "Lagoon Villa", "price": "₱18,500/night", "desc": "Lagoon access, King bed, 65 sqm"},
            {"type": "Cliff Suite",  "price": "₱28,000/night", "desc": "Cliff-edge pool, King bed, 90 sqm"},
        ],
        "gallery": ["boracay.jpg","cebu.jpg","baguio.jpg","davao.jpg"]
    },
]

destinations = [
    {"name": "Manila",  "image": "manila.jpg"},
    {"name": "Cebu",    "image": "cebu.jpg"},
    {"name": "Davao",   "image": "davao.jpg"},
    {"name": "Boracay", "image": "boracay.jpg"},
    {"name": "Baguio",  "image": "baguio.jpg"},
]

# ── HELPERS ───────────────────────────────────────────────────────────────────

def extract_price_value(price_str):
    """Extract numeric value from a price string like '₱4,500/night'."""
    nums = re.sub(r"[^\d.]", "", price_str.replace(",", ""))
    try:
        return float(nums)
    except Exception:
        return 0.0

def login_required(fn):
    """Decorator: redirect to login if not a user session."""
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/")
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    """Decorator: redirect to admin login if not an admin session."""
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect("/admin/login")
        return fn(*args, **kwargs)
    return wrapper

# ── USER ROUTES ───────────────────────────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def login():
    if session.get("user"):
        return redirect("/home")
    error = None
    if request.method == "POST":
        email    = request.form["email"].strip()
        password = request.form["password"]
        conn = get_db()
        c    = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()
        if user:
            session["user"] = email
            session["name"] = user["name"] if user["name"] else email.split("@")[0]
            return redirect("/home")
        else:
            error = "Invalid email or password. Please try again."
    return render_template("login.html", error=error)

@app.route("/register", methods=["POST"])
def register():
    name     = request.form.get("name", "").strip()
    email    = request.form["email"].strip()
    password = request.form["password"]
    if not name or not email or not password:
        return redirect("/?reg_error=missing")
    try:
        conn = get_db()
        c    = conn.cursor()
        c.execute("INSERT INTO users(email,password,name) VALUES(?,?,?)", (email, password, name))
        conn.commit()
        conn.close()
        return redirect("/?registered=1")
    except sqlite3.IntegrityError:
        return redirect("/?reg_error=exists")

@app.route("/home")
@login_required
def home():
    return render_template("home.html",
                           destinations=destinations,
                           all_hotels=hotels_data,
                           user=session.get("name", session["user"]))

@app.route("/hotels")
def hotels():
    location = request.args.get("location", "").strip()
    htype    = request.args.get("type", "").strip()
    results  = hotels_data
    if location:
        results = [h for h in results if location.lower() in h["location"].lower()]
    if htype:
        results = [h for h in results if h["type"] == htype]
    return render_template("hotels.html",
                           hotels=results,
                           query=location,
                           htype=htype,
                           user=session.get("name", ""))

@app.route("/hotel/<name>")
@login_required
def hotel_detail(name):
    # Fix: Decode name and use robust matching
    from urllib.parse import unquote
    decoded_name = unquote(name).strip()
    hotel = next((h for h in hotels_data if h["name"].lower() == decoded_name.lower()), None)
    
    if not hotel:
        # Fallback: try matching without spaces if exact match fails
        hotel = next((h for h in hotels_data if h["name"].replace(" ","").lower() == decoded_name.replace(" ","").lower()), None)
        
    if not hotel:
        return redirect("/hotels")
        
    others = [h for h in hotels_data if h["name"] != hotel["name"]][:3]
    return render_template("hotel_detail.html",
                           hotel=hotel,
                           others=others,
                           user=session.get("name", ""))

@app.route("/book/<hotel_name>")
@login_required
def book(hotel_name):
    hotel = next((h for h in hotels_data if h["name"] == hotel_name), None)
    if not hotel:
        return redirect("/hotels")
    room_type = request.args.get("room", hotel["rooms"][0]["type"])
    room = next((r for r in hotel["rooms"] if r["type"] == room_type), hotel["rooms"][0])
    return render_template("booking.html",
                           hotel=hotel,
                           room=room,
                           user=session.get("name", ""),
                           email=session.get("user", ""))

@app.route("/confirm", methods=["POST"])
@login_required
def confirm():
    hotel_name = request.form.get("hotel", "")
    check_in   = request.form.get("check_in", "")
    check_out  = request.form.get("check_out", "")
    guests     = request.form.get("guests", 1)
    room_type  = request.form.get("room_type", "")
    price_str  = request.form.get("price", "")

    if not hotel_name or not check_in or not check_out:
        return redirect("/hotels")

    # Calculate Nights
    from datetime import datetime
    try:
        d1 = datetime.strptime(check_in, "%Y-%m-%d")
        d2 = datetime.strptime(check_out, "%Y-%m-%d")
        nights = (d2 - d1).days
        if nights < 1: nights = 1
    except:
        nights = 1

    price_val = extract_price_value(price_str)
    total_price = price_val * nights
    ref_code = "LX" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    hotel = next((h for h in hotels_data if h["name"] == hotel_name), None)
    if not hotel: return redirect("/hotels")

    conn = get_db()
    c    = conn.cursor()
    c.execute("""INSERT INTO bookings(user,hotel,location,check_in,check_out,guests,room_type,price,ref_code,status,price_value)
                 VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
              (session["user"], hotel_name, hotel["location"],
               check_in, check_out, guests, room_type, f"₱{total_price:,.0f}", ref_code, "pending", total_price))
    conn.commit()
    conn.close()

    return render_template("confirmation.html",
                           hotel=hotel,
                           check_in=check_in,
                           check_out=check_out,
                           guests=guests,
                           nights=nights,
                           room_type=room_type,
                           total_price=f"₱{total_price:,.0f}",
                           ref_code=ref_code,
                           user=session.get("name", ""),
                           others=[h for h in hotels_data if h["name"] != hotel_name][:3])

@app.route("/my-bookings")
@login_required
def my_bookings():
    conn = get_db()
    c    = conn.cursor()
    c.execute("SELECT * FROM bookings WHERE user=? ORDER BY id DESC", (session["user"],))
    bookings = [dict(row) for row in c.fetchall()]
    conn.close()
    return render_template("my_bookings.html",
                           bookings=bookings,
                           user=session.get("name", ""))

@app.route("/delete-booking/<int:booking_id>", methods=["POST"])
@login_required
def delete_booking(booking_id):
    conn = get_db()
    c    = conn.cursor()
    c.execute("DELETE FROM bookings WHERE id=? AND user=?", (booking_id, session["user"]))
    conn.commit()
    conn.close()
    return redirect("/my-bookings")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ── ADMIN ROUTES ──────────────────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("is_admin"):
        return redirect("/admin")
    error = None
    if request.method == "POST":
        email    = request.form["email"].strip()
        password = request.form["password"]
        conn = get_db()
        c    = conn.cursor()
        c.execute("SELECT * FROM admins WHERE email=? AND password=?", (email, password))
        admin = c.fetchone()
        conn.close()
        if admin:
            session["is_admin"]   = True
            session["admin_name"] = admin["name"]
            return redirect("/admin")
        else:
            error = "Invalid admin credentials."
    return render_template("admin_login.html", error=error)

@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = get_db()
    c    = conn.cursor()

    # Stats
    c.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM bookings WHERE status='pending'")
    total_pending = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM bookings WHERE status='accepted'")
    total_accepted = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM bookings WHERE status='rejected'")
    total_rejected = c.fetchone()[0]

    c.execute("SELECT COUNT(DISTINCT user) FROM bookings")
    total_users_booked = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]

    # Total profit from accepted bookings
    c.execute("SELECT COALESCE(SUM(price_value),0) FROM bookings WHERE status='accepted'")
    total_profit = c.fetchone()[0]

    # Most booked hotel
    c.execute("SELECT hotel, COUNT(*) as cnt FROM bookings GROUP BY hotel ORDER BY cnt DESC LIMIT 1")
    top_hotel_row = c.fetchone()
    top_hotel = top_hotel_row["hotel"] if top_hotel_row else "—"

    # All bookings with user info
    c.execute("""SELECT b.*, u.name as guest_name
                 FROM bookings b
                 LEFT JOIN users u ON b.user = u.email
                 ORDER BY b.id DESC""")
    bookings = [dict(row) for row in c.fetchall()]

    # All users
    c.execute("SELECT * FROM users ORDER BY id DESC")
    users = [dict(row) for row in c.fetchall()]

    # Revenue per hotel (accepted bookings only)
    c.execute("""SELECT hotel, COUNT(*) as cnt, COALESCE(SUM(price_value),0) as revenue
                 FROM bookings WHERE status='accepted' GROUP BY hotel ORDER BY revenue DESC""")
    hotel_stats = [dict(row) for row in c.fetchall()]

    # All bookings per hotel for chart
    c.execute("SELECT hotel, COUNT(*) as cnt FROM bookings GROUP BY hotel ORDER BY cnt DESC")
    booking_stats = [dict(row) for row in c.fetchall()]

    conn.close()

    return render_template("admin_dashboard.html",
                           total_bookings=total_bookings,
                           total_pending=total_pending,
                           total_accepted=total_accepted,
                           total_rejected=total_rejected,
                           total_users=total_users,
                           total_users_booked=total_users_booked,
                           total_profit=total_profit,
                           top_hotel=top_hotel,
                           bookings=bookings,
                           users=users,
                           hotel_stats=hotel_stats,
                           booking_stats=booking_stats,
                           admin_name=session.get("admin_name", "Admin"))

@app.route("/admin/booking/<int:booking_id>/accept", methods=["POST"])
@admin_required
def admin_accept_booking(booking_id):
    conn = get_db()
    c    = conn.cursor()
    c.execute("UPDATE bookings SET status='accepted' WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

@app.route("/admin/booking/<int:booking_id>/reject", methods=["POST"])
@admin_required
def admin_reject_booking(booking_id):
    conn = get_db()
    c    = conn.cursor()
    c.execute("UPDATE bookings SET status='rejected' WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

@app.route("/admin/delete-booking/<int:booking_id>", methods=["POST"])
@admin_required
def admin_delete_booking(booking_id):
    conn = get_db()
    c    = conn.cursor()
    c.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

@app.route("/admin/delete-user/<int:user_id>", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    conn = get_db()
    c    = conn.cursor()
    # Also delete their bookings
    c.execute("SELECT email FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    if row:
        c.execute("DELETE FROM bookings WHERE user=?", (row["email"],))
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    session.pop("admin_name", None)
    return redirect("/admin/login")

# ── MAIN ──────────────────────────────────────────────────────────────────────

def _open_browser():
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    # Auto-open browser 1.5 s after Flask starts
    threading.Timer(1.5, _open_browser).start()
    app.run(debug=False, host="0.0.0.0", port=5000)