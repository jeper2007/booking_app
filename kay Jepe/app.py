# pyrefly: ignore [missing-import]
from flask import Flask, render_template, request, redirect, session, url_for
import random, string, re, os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "luxstay_secret_2024")

# ── DATABASE ──────────────────────────────────────────────────────────────────
# If DATABASE_URL is set (Supabase/PostgreSQL on Vercel): use PostgreSQL.
# Otherwise fall back to local SQLite for development.
DATABASE_URL = os.environ.get("DATABASE_URL", "")
USE_PG = bool(DATABASE_URL)

if USE_PG:
    import psycopg2
    import psycopg2.extras
    PH = "%s"   # PostgreSQL placeholder
    def get_db():
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        return conn
    def _cursor(conn):
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
else:
    import sqlite3
    PH = "?"    # SQLite placeholder
    IF_VERCEL = os.environ.get("VERCEL")
    if IF_VERCEL:
        DB_PATH = "/tmp/database.db"
        if not os.path.exists(DB_PATH):
            try:
                import shutil
                SOURCE_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")
                if os.path.exists(SOURCE_DB):
                    shutil.copy(SOURCE_DB, DB_PATH)
            except Exception:
                pass
    else:
        DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")
    def get_db():
        db_dir = os.path.dirname(DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    def _cursor(conn):
        return conn.cursor()

def init_db():
    conn = get_db()
    c = _cursor(conn)
    if USE_PG:
        c.execute("""CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS bookings(
            id SERIAL PRIMARY KEY, "user" TEXT, hotel TEXT, location TEXT,
            check_in TEXT, check_out TEXT, guests INTEGER,
            room_type TEXT, price TEXT, ref_code TEXT,
            status TEXT DEFAULT 'pending', price_value REAL DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS admins(
            id SERIAL PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT)""")
    else:
        c.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT, name TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS bookings(
            id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, hotel TEXT, location TEXT,
            check_in TEXT, check_out TEXT, guests INTEGER,
            room_type TEXT, price TEXT, ref_code TEXT,
            status TEXT DEFAULT 'pending', price_value REAL DEFAULT 0)""")
        for col, defn in [("status","TEXT DEFAULT 'pending'"),("price_value","REAL DEFAULT 0")]:
            try:
                c.execute(f"ALTER TABLE bookings ADD COLUMN {col} {defn}")
            except Exception:
                pass
        c.execute("""CREATE TABLE IF NOT EXISTS admins(
            id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT, name TEXT)""")
    # Seed default admin if none exists
    c.execute("SELECT COUNT(*) as cnt FROM admins")
    row = c.fetchone()
    cnt = row["cnt"] if USE_PG else row[0]
    if cnt == 0:
        c.execute(f"INSERT INTO admins(email,password,name) VALUES({PH},{PH},{PH})",
                  ("admin@luxstay.ph", "admin123", "LuxStay Admin"))
    conn.commit()
    conn.close()

init_db()

# ── HOTEL DATA ────────────────────────────────────────────────────────────────
# total_rooms = maximum bookable rooms per room type
hotels_data = [
    {
        "name": "Hotel Manila Bay", "location": "Manila",
        "image": "manila.jpg", "price": "₱4,500", "rating": 4.8, "type": "City",
        "description": "Experience the vibrant heart of Metro Manila with breathtaking bay views, world-class dining, and modern amenities.",
        "amenities": ["Free WiFi","Pool","Spa","Gym","Restaurant","Bar"],
        "rooms": [
            {"type":"Deluxe Room",    "price":"₱4,500/night",  "desc":"City view, King bed, 35 sqm",       "total_rooms":15},
            {"type":"Superior Suite", "price":"₱7,200/night",  "desc":"Bay view, King bed, 55 sqm",        "total_rooms":8},
            {"type":"Executive Suite","price":"₱12,000/night", "desc":"Panoramic view, 2 beds, 80 sqm",    "total_rooms":4},
        ],
        "gallery": ["manila.jpg","cebu.jpg","davao.jpg","boracay.jpg"]
    },
    {
        "name": "Cebu Island Resort", "location": "Cebu",
        "image": "cebu.jpg", "price": "₱6,800", "rating": 4.9, "type": "Beach",
        "description": "A tropical paradise on the shores of Cebu, offering pristine white sands, coral reefs, and luxurious island living.",
        "amenities": ["Private Beach","Snorkeling","Free WiFi","Pool","Spa","Water Sports"],
        "rooms": [
            {"type":"Garden Room",    "price":"₱6,800/night",  "desc":"Garden view, Queen bed, 30 sqm",    "total_rooms":20},
            {"type":"Beach Villa",    "price":"₱11,500/night", "desc":"Beachfront, King bed, 60 sqm",      "total_rooms":10},
            {"type":"Ocean Bungalow", "price":"₱18,000/night", "desc":"Overwater, King bed, 70 sqm",       "total_rooms":5},
        ],
        "gallery": ["cebu.jpg","boracay.jpg","manila.jpg","davao.jpg"]
    },
    {
        "name": "Davao Garden Inn", "location": "Davao",
        "image": "davao.jpg", "price": "₱3,200", "rating": 4.5, "type": "City",
        "description": "Nestled at the foot of Mount Apo, Davao Garden Inn offers a serene escape with lush tropical gardens and Filipino hospitality.",
        "amenities": ["Free WiFi","Garden","Restaurant","Gym","Meeting Rooms"],
        "rooms": [
            {"type":"Standard Room",  "price":"₱3,200/night", "desc":"Garden view, Double bed, 25 sqm",   "total_rooms":25},
            {"type":"Deluxe Room",    "price":"₱5,000/night", "desc":"Mountain view, King bed, 38 sqm",   "total_rooms":12},
            {"type":"Family Suite",   "price":"₱8,500/night", "desc":"Full suite, 2 beds, 65 sqm",        "total_rooms":6},
        ],
        "gallery": ["davao.jpg","baguio.jpg","manila.jpg","cebu.jpg"]
    },
    {
        "name": "Boracay Pearl Resort", "location": "Boracay",
        "image": "boracay.jpg", "price": "₱9,500", "rating": 4.9, "type": "Beach",
        "description": "Set on the world-famous White Beach of Boracay, Pearl Resort epitomizes tropical luxury with sunset views.",
        "amenities": ["Beachfront","Infinity Pool","Free WiFi","Spa","Water Sports","Nightclub"],
        "rooms": [
            {"type":"Beach Room",    "price":"₱9,500/night",  "desc":"Sea view, Queen bed, 35 sqm",       "total_rooms":18},
            {"type":"Premium Suite", "price":"₱16,000/night", "desc":"Beachfront, King bed, 65 sqm",      "total_rooms":7},
            {"type":"Villa",         "price":"₱25,000/night", "desc":"Private pool villa, King bed, 100 sqm","total_rooms":3},
        ],
        "gallery": ["boracay.jpg","cebu.jpg","manila.jpg","davao.jpg"]
    },
    {
        "name": "Baguio Pine Lodge", "location": "Baguio",
        "image": "baguio.jpg", "price": "₱3,800", "rating": 4.6, "type": "Mountain",
        "description": "Escape the heat in Baguio's cool mountain embrace. Pine Lodge offers cozy rooms amid towering pine trees.",
        "amenities": ["Fireplace","Mountain View","Free WiFi","Restaurant","Garden"],
        "rooms": [
            {"type":"Cozy Room",     "price":"₱3,800/night", "desc":"Forest view, Queen bed, 28 sqm",     "total_rooms":20},
            {"type":"Superior Room", "price":"₱5,500/night", "desc":"Mountain view, King bed, 40 sqm",    "total_rooms":10},
            {"type":"Chalet Suite",  "price":"₱9,000/night", "desc":"Private deck, 2 beds, 70 sqm",       "total_rooms":4},
        ],
        "gallery": ["baguio.jpg","davao.jpg","manila.jpg","cebu.jpg"]
    },
    {
        "name": "Palawan Horizon Hotel", "location": "Palawan",
        "image": "boracay.jpg", "price": "₱11,200", "rating": 5.0, "type": "Beach",
        "description": "In the last frontier of the Philippines, Horizon Hotel offers unmatched natural beauty and eco-luxury stays.",
        "amenities": ["Diving Center","Kayaking","Eco Pool","Restaurant","Free WiFi","Spa"],
        "rooms": [
            {"type":"Nature Room",  "price":"₱11,200/night", "desc":"Jungle view, King bed, 40 sqm",      "total_rooms":12},
            {"type":"Lagoon Villa", "price":"₱18,500/night", "desc":"Lagoon access, King bed, 65 sqm",    "total_rooms":6},
            {"type":"Cliff Suite",  "price":"₱28,000/night", "desc":"Cliff-edge pool, King bed, 90 sqm",  "total_rooms":2},
        ],
        "gallery": ["boracay.jpg","cebu.jpg","baguio.jpg","davao.jpg"]
    },
]

destinations = [
    {"name":"Manila","image":"manila.jpg"}, {"name":"Cebu","image":"cebu.jpg"},
    {"name":"Davao","image":"davao.jpg"},   {"name":"Boracay","image":"boracay.jpg"},
    {"name":"Baguio","image":"baguio.jpg"},
]

# ── HELPERS ───────────────────────────────────────────────────────────────────

def extract_price_value(price_str):
    nums = re.sub(r"[^\d.]", "", price_str.replace(",", ""))
    try:
        return float(nums)
    except Exception:
        return 0.0

def get_available_rooms(hotel_name, room_type=None):
    """Return dict of {room_type: available_count} or single count for one room_type."""
    hotel = next((h for h in hotels_data if h["name"].lower() == hotel_name.lower()), None)
    if not hotel:
        return {} if room_type is None else 0
    conn = get_db()
    c = _cursor(conn)
    result = {}
    col = '"user"' if USE_PG else 'user'
    for room in hotel["rooms"]:
        c.execute(
            f"SELECT COUNT(*) as cnt FROM bookings WHERE hotel={PH} AND room_type={PH} AND status != 'rejected'",
            (hotel_name, room["type"])
        )
        row = c.fetchone()
        booked = row["cnt"] if USE_PG else row[0]
        result[room["type"]] = max(0, room["total_rooms"] - booked)
    conn.close()
    if room_type:
        return result.get(room_type, 0)
    return result

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login", next=request.full_path))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect("/admin/login")
        return fn(*args, **kwargs)
    return wrapper

# ── USER ROUTES ───────────────────────────────────────────────────────────────

@app.route("/", methods=["GET","POST"])
def login():
    if session.get("user"):
        return redirect("/home")
    error = None
    if request.method == "POST":
        email    = request.form["email"].strip()
        password = request.form["password"]
        next_url = request.form.get("next", "").strip()
        conn = get_db(); c = _cursor(conn)
        c.execute(f"SELECT * FROM users WHERE email={PH} AND password={PH}", (email, password))
        user = c.fetchone(); conn.close()
        if user:
            session["user"] = email
            session["name"] = user["name"] if user["name"] else email.split("@")[0]
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect("/home")
        error = "Invalid email or password. Please try again."
    next_url = request.args.get("next", "")
    return render_template("login.html", error=error, next_url=next_url)

@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name","").strip()
    email = request.form["email"].strip()
    password = request.form["password"]
    if not name or not email or not password:
        return redirect("/?reg_error=missing")
    try:
        conn = get_db(); c = _cursor(conn)
        c.execute(f"INSERT INTO users(email,password,name) VALUES({PH},{PH},{PH})", (email, password, name))
        conn.commit(); conn.close()
        return redirect("/?registered=1")
    except Exception:
        return redirect("/?reg_error=exists")

@app.route("/home")
@login_required
def home():
    return render_template("home.html", destinations=destinations,
                           all_hotels=hotels_data,
                           user=session.get("name", session["user"]))

@app.route("/hotels")
def hotels():
    location = request.args.get("location","").strip()
    htype    = request.args.get("type","").strip()
    results  = hotels_data
    if location:
        results = [h for h in results if location.lower() in h["location"].lower()]
    if htype:
        results = [h for h in results if h["type"] == htype]
    # Compute total available rooms per hotel for the cards
    hotel_avail = {}
    for h in results:
        avail = get_available_rooms(h["name"])
        hotel_avail[h["name"]] = sum(avail.values())
    return render_template("hotels.html", hotels=results, query=location, htype=htype,
                           user=session.get("name",""), is_logged_in=bool(session.get("user")),
                           hotel_avail=hotel_avail)

@app.route("/hotel/<name>")
def hotel_detail(name):
    from urllib.parse import unquote_plus
    decoded = unquote_plus(name).strip()
    hotel = next((h for h in hotels_data if h["name"].lower() == decoded.lower()), None)
    if not hotel:
        hotel = next((h for h in hotels_data if h["name"].replace(" ","").lower() == decoded.replace(" ","").lower()), None)
    if not hotel:
        return redirect("/hotels")
    room_avail = get_available_rooms(hotel["name"])
    others = [h for h in hotels_data if h["name"] != hotel["name"]][:3]
    return render_template("hotel_detail.html", hotel=hotel, others=others,
                           user=session.get("name",""),
                           is_logged_in=bool(session.get("user")),
                           room_avail=room_avail)

@app.route("/book/<hotel_name>")
@login_required
def book(hotel_name):
    from urllib.parse import unquote_plus
    hotel_name = unquote_plus(hotel_name).strip()
    hotel = next((h for h in hotels_data if h["name"].lower() == hotel_name.lower()), None)
    if not hotel:
        return redirect("/hotels")
    room_type = unquote_plus(request.args.get("room", hotel["rooms"][0]["type"]).strip())
    room = next((r for r in hotel["rooms"] if r["type"].lower() == room_type.lower()), hotel["rooms"][0])
    conn = get_db()
    c = _cursor(conn)
    c.execute(f"SELECT COUNT(*) as cnt FROM bookings WHERE hotel={PH} AND room_type={PH} AND status != 'rejected'", (hotel_name, room["type"]))
    avail_row = c.fetchone()
    conn.close()
    avail = get_available_rooms(hotel["name"], room["type"])
    if avail <= 0:
        return redirect(f"/hotel/{hotel_name}?no_avail=1")
    return render_template("booking.html", hotel=hotel, room=room,
                           avail=avail, user=session.get("name",""), email=session.get("user",""))

@app.route("/confirm", methods=["POST"])
@login_required
def confirm():
    hotel_name = request.form.get("hotel","")
    check_in   = request.form.get("check_in","")
    check_out  = request.form.get("check_out","")
    guests     = request.form.get("guests", 1)
    room_type  = request.form.get("room_type","")
    price      = request.form.get("price","")
    if not hotel_name or not check_in or not check_out:
        return redirect("/hotels")
    hotel = next((h for h in hotels_data if h["name"].lower() == hotel_name.strip().lower()), None)
    if not hotel:
        return redirect("/hotels")
    ref_code = "LX" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    conn = get_db(); c = _cursor(conn)
    price_val = extract_price_value(price)
    user_col = '"user"' if USE_PG else 'user'
    c.execute(f"""INSERT INTO bookings({user_col},hotel,location,check_in,check_out,guests,room_type,price,ref_code,status,price_value)
                 VALUES({PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH})""",
              (session["user"], hotel_name, hotel["location"],
               check_in, check_out, guests, room_type, price, ref_code, "pending", price_val))
    conn.commit(); conn.close()
    return render_template("confirmation.html", hotel=hotel, check_in=check_in,
                           check_out=check_out, guests=guests, room_type=room_type,
                           price=price, ref_code=ref_code, user=session.get("name",""),
                           others=[h for h in hotels_data if h["name"] != hotel_name][:3])

@app.route("/my-bookings")
@login_required
def my_bookings():
    conn = get_db(); c = _cursor(conn)
    user_col = '"user"' if USE_PG else 'user'
    c.execute(f"SELECT * FROM bookings WHERE {user_col}={PH} ORDER BY id DESC", (session["user"],))
    bookings = [dict(row) for row in c.fetchall()]
    conn.close()
    return render_template("my_bookings.html", bookings=bookings, user=session.get("name",""))

@app.route("/delete-booking/<int:booking_id>", methods=["POST"])
@login_required
def delete_booking(booking_id):
    conn = get_db(); c = _cursor(conn)
    user_col = '"user"' if USE_PG else 'user'
    c.execute(f"DELETE FROM bookings WHERE id={PH} AND {user_col}={PH}", (booking_id, session["user"]))
    conn.commit(); conn.close()
    return redirect("/my-bookings")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ── ADMIN ROUTES ──────────────────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if session.get("is_admin"):
        return redirect("/admin")
    error = None
    if request.method == "POST":
        email = request.form["email"].strip(); password = request.form["password"]
        conn = get_db(); c = _cursor(conn)
        c.execute(f"SELECT * FROM admins WHERE email={PH} AND password={PH}", (email, password))
        admin = c.fetchone(); conn.close()
        if admin:
            session["is_admin"] = True; session["admin_name"] = admin["name"]
            return redirect("/admin")
        error = "Invalid admin credentials."
    return render_template("admin_login.html", error=error)

@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = get_db(); c = _cursor(conn)
    user_col = '"user"' if USE_PG else 'user'
    def q(sql):
        c.execute(sql)
        row = c.fetchone()
        return row["cnt"] if USE_PG else row[0]
    total_bookings    = q("SELECT COUNT(*) as cnt FROM bookings")
    total_pending     = q("SELECT COUNT(*) as cnt FROM bookings WHERE status='pending'")
    total_accepted    = q("SELECT COUNT(*) as cnt FROM bookings WHERE status='accepted'")
    total_rejected    = q("SELECT COUNT(*) as cnt FROM bookings WHERE status='rejected'")
    total_users_booked= q(f"SELECT COUNT(DISTINCT {user_col}) as cnt FROM bookings")
    total_users       = q("SELECT COUNT(*) as cnt FROM users")
    c.execute("SELECT COALESCE(SUM(price_value),0) as s FROM bookings WHERE status='accepted'")
    profit_row = c.fetchone()
    total_profit = profit_row["s"] if USE_PG else profit_row[0]
    c.execute("SELECT hotel, COUNT(*) as cnt FROM bookings GROUP BY hotel ORDER BY cnt DESC LIMIT 1")
    r = c.fetchone(); top_hotel = r["hotel"] if r else "—"
    join_col = 'b."user"' if USE_PG else 'b.user'
    c.execute(f"""SELECT b.*, u.name as guest_name FROM bookings b
                 LEFT JOIN users u ON {join_col}=u.email ORDER BY b.id DESC""")
    bookings = [dict(r) for r in c.fetchall()]
    c.execute("SELECT * FROM users ORDER BY id DESC")
    users = [dict(r) for r in c.fetchall()]
    c.execute("""SELECT hotel, COUNT(*) as cnt, COALESCE(SUM(price_value),0) as revenue
                 FROM bookings WHERE status='accepted' GROUP BY hotel ORDER BY revenue DESC""")
    hotel_stats = [dict(r) for r in c.fetchall()]
    c.execute("SELECT hotel, COUNT(*) as cnt FROM bookings GROUP BY hotel ORDER BY cnt DESC")
    booking_stats = [dict(r) for r in c.fetchall()]
    conn.close()
    return render_template("admin_dashboard.html",
                           total_bookings=total_bookings, total_pending=total_pending,
                           total_accepted=total_accepted, total_rejected=total_rejected,
                           total_users=total_users, total_users_booked=total_users_booked,
                           total_profit=total_profit, top_hotel=top_hotel,
                           bookings=bookings, users=users,
                           hotel_stats=hotel_stats, booking_stats=booking_stats,
                           admin_name=session.get("admin_name","Admin"))

@app.route("/admin/booking/<int:bid>/accept", methods=["POST"])
@admin_required
def admin_accept_booking(bid):
    conn = get_db(); c = _cursor(conn)
    c.execute(f"UPDATE bookings SET status='accepted' WHERE id={PH}", (bid,))
    conn.commit(); conn.close(); return redirect("/admin")

@app.route("/admin/booking/<int:bid>/reject", methods=["POST"])
@admin_required
def admin_reject_booking(bid):
    conn = get_db(); c = _cursor(conn)
    c.execute(f"UPDATE bookings SET status='rejected' WHERE id={PH}", (bid,))
    conn.commit(); conn.close(); return redirect("/admin")

@app.route("/admin/delete-booking/<int:bid>", methods=["POST"])
@admin_required
def admin_delete_booking(bid):
    conn = get_db(); c = _cursor(conn)
    c.execute(f"DELETE FROM bookings WHERE id={PH}", (bid,))
    conn.commit(); conn.close(); return redirect("/admin")

@app.route("/admin/delete-user/<int:uid>", methods=["POST"])
@admin_required
def admin_delete_user(uid):
    conn = get_db(); c = _cursor(conn)
    user_col = '"user"' if USE_PG else 'user'
    c.execute(f"SELECT email FROM users WHERE id={PH}", (uid,))
    row = c.fetchone()
    if row:
        c.execute(f"DELETE FROM bookings WHERE {user_col}={PH}", (row["email"],))
    c.execute(f"DELETE FROM users WHERE id={PH}", (uid,))
    conn.commit(); conn.close(); return redirect("/admin")

@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None); session.pop("admin_name", None)
    return redirect("/admin/login")

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)