html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LuxStay Admin Dashboard</title>
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,sans-serif;background:#0f0f1a;color:#e0e0e0;min-height:100vh;display:flex}
/* SIDEBAR */
.sidebar{width:240px;min-height:100vh;background:#13132a;border-right:1px solid rgba(255,255,255,.06);display:flex;flex-direction:column;position:fixed;top:0;left:0;z-index:100}
.sidebar-logo{padding:28px 24px;border-bottom:1px solid rgba(255,255,255,.06)}
.sidebar-logo h2{color:#fff;font-size:1.25rem;font-weight:800}.sidebar-logo h2 span{color:#f5a623}
.sidebar-logo p{color:rgba(255,255,255,.3);font-size:.72rem;margin-top:2px;letter-spacing:.5px;text-transform:uppercase}
.sidebar-nav{flex:1;padding:16px 12px}
.nav-item{display:flex;align-items:center;gap:12px;padding:11px 14px;border-radius:10px;color:rgba(255,255,255,.5);font-size:.88rem;font-weight:500;cursor:pointer;transition:.2s ease;margin-bottom:4px;text-decoration:none}
.nav-item:hover{background:rgba(255,255,255,.06);color:#fff}
.nav-item.active{background:linear-gradient(135deg,rgba(245,166,35,.2),rgba(233,69,96,.1));color:#f5a623;border:1px solid rgba(245,166,35,.2)}
.nav-item .ico{font-size:1.1rem;width:20px;text-align:center}
.sidebar-footer{padding:16px 12px;border-top:1px solid rgba(255,255,255,.06)}
/* MAIN */
.main{margin-left:240px;flex:1;min-height:100vh;display:flex;flex-direction:column}
.topbar{background:#13132a;border-bottom:1px solid rgba(255,255,255,.06);padding:0 32px;height:64px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:50}
.topbar h1{color:#fff;font-size:1.1rem;font-weight:700}
.admin-pill{display:flex;align-items:center;gap:10px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);border-radius:50px;padding:6px 16px 6px 10px}
.admin-avatar{width:30px;height:30px;border-radius:50%;background:linear-gradient(135deg,#f5a623,#e67e22);display:flex;align-items:center;justify-content:center;font-size:.85rem;font-weight:700;color:#fff}
.admin-pill span{font-size:.85rem;color:rgba(255,255,255,.7)}
.content{padding:32px;flex:1}
/* STAT CARDS */
.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-bottom:32px}
.stat-card{background:#1a1a2e;border:1px solid rgba(255,255,255,.07);border-radius:16px;padding:24px;transition:.25s ease;animation:fadeUp .5s ease both}
.stat-card:hover{transform:translateY(-4px);border-color:rgba(245,166,35,.25)}
.stat-card .ico{font-size:1.6rem;margin-bottom:12px}
.stat-card .val{font-size:2rem;font-weight:800;color:#fff;margin-bottom:4px}
.stat-card .lbl{font-size:.78rem;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.5px}
.stat-card.gold{border-color:rgba(245,166,35,.2)}.stat-card.red{border-color:rgba(233,69,96,.2)}.stat-card.blue{border-color:rgba(66,153,225,.2)}.stat-card.green{border-color:rgba(72,187,120,.2)}
/* TABS */
.tab-bar{display:flex;gap:4px;background:#13132a;border-radius:50px;padding:4px;margin-bottom:24px;width:fit-content}
.tab{padding:8px 20px;border-radius:50px;font-size:.85rem;font-weight:600;cursor:pointer;color:rgba(255,255,255,.4);transition:.2s;border:none;background:transparent;font-family:inherit}
.tab.active{background:rgba(245,166,35,.15);color:#f5a623;border:1px solid rgba(245,166,35,.25)}
/* TABLE */
.table-card{background:#1a1a2e;border:1px solid rgba(255,255,255,.07);border-radius:16px;overflow:hidden;animation:fadeIn .5s ease}
.table-header{padding:20px 24px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(255,255,255,.06)}
.table-header h3{color:#fff;font-size:1rem;font-weight:700}
.search-input{padding:8px 14px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;font-size:.85rem;font-family:inherit;outline:none;width:220px}
.search-input::placeholder{color:rgba(255,255,255,.25)}
table{width:100%;border-collapse:collapse}
thead tr{background:rgba(255,255,255,.03)}
th{padding:12px 16px;text-align:left;font-size:.75rem;font-weight:700;color:rgba(255,255,255,.3);letter-spacing:.5px;text-transform:uppercase;border-bottom:1px solid rgba(255,255,255,.06)}
td{padding:13px 16px;font-size:.85rem;color:rgba(255,255,255,.75);border-bottom:1px solid rgba(255,255,255,.04);vertical-align:middle}
tr:last-child td{border-bottom:none}
tr:hover td{background:rgba(255,255,255,.02)}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.72rem;font-weight:700}
.badge-beach{background:rgba(66,153,225,.15);color:#63b3ed}
.badge-city{background:rgba(72,187,120,.15);color:#68d391}
.badge-mountain{background:rgba(245,166,35,.15);color:#f5a623}
.badge-ref{background:rgba(233,69,96,.12);color:#fc8181;font-family:monospace;letter-spacing:1px}
.btn-del{background:rgba(233,69,96,.15);color:#fc8181;border:1px solid rgba(233,69,96,.25);padding:5px 12px;border-radius:6px;font-size:.78rem;font-weight:600;cursor:pointer;font-family:inherit;transition:.2s}
.btn-del:hover{background:rgba(233,69,96,.3)}
.empty-row td{text-align:center;padding:40px;color:rgba(255,255,255,.25)}
/* CHART BAR */
.chart-wrap{margin-top:24px}
.bar-row{display:flex;align-items:center;gap:14px;margin-bottom:12px}
.bar-label{width:160px;font-size:.82rem;color:rgba(255,255,255,.6);flex-shrink:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar-track{flex:1;background:rgba(255,255,255,.06);border-radius:50px;height:10px;overflow:hidden}
.bar-fill{height:100%;background:linear-gradient(90deg,#f5a623,#e94560);border-radius:50px;transition:width .6s ease}
.bar-count{width:30px;text-align:right;font-size:.82rem;font-weight:700;color:#f5a623}
@keyframes fadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
</style>
</head>
<body>

<!-- SIDEBAR -->
<aside class="sidebar">
  <div class="sidebar-logo">
    <h2>Lux<span>Stay</span></h2>
    <p>Admin Dashboard</p>
  </div>
  <nav class="sidebar-nav">
    <a class="nav-item active" onclick="showTab('bookings')"><span class="ico">📋</span> All Bookings</a>
    <a class="nav-item" onclick="showTab('users')"><span class="ico">👥</span> Users</a>
    <a class="nav-item" onclick="showTab('analytics')"><span class="ico">📊</span> Analytics</a>
    <a class="nav-item" href="/hotels" target="_blank"><span class="ico">🏨</span> View Site</a>
  </nav>
  <div class="sidebar-footer">
    <a class="nav-item" href="/admin/logout"><span class="ico">🚪</span> Logout</a>
  </div>
</aside>

<!-- MAIN CONTENT -->
<div class="main">
  <header class="topbar">
    <h1 id="page-title">All Bookings</h1>
    <div class="admin-pill">
      <div class="admin-avatar">A</div>
      <span>{{ admin_name }}</span>
    </div>
  </header>

  <div class="content">
    <!-- STAT CARDS -->
    <div class="stats-grid">
      <div class="stat-card gold" style="animation-delay:.0s">
        <div class="ico">📋</div>
        <div class="val">{{ total_bookings }}</div>
        <div class="lbl">Total Bookings</div>
      </div>
      <div class="stat-card blue" style="animation-delay:.1s">
        <div class="ico">👥</div>
        <div class="val">{{ total_users }}</div>
        <div class="lbl">Registered Users</div>
      </div>
      <div class="stat-card green" style="animation-delay:.2s">
        <div class="ico">🏆</div>
        <div class="val">{{ total_users_booked }}</div>
        <div class="lbl">Active Guests</div>
      </div>
      <div class="stat-card red" style="animation-delay:.3s">
        <div class="ico">⭐</div>
        <div class="val" style="font-size:1rem;margin-top:6px">{{ top_hotel }}</div>
        <div class="lbl">Top Hotel</div>
      </div>
    </div>

    <!-- BOOKINGS TAB -->
    <div id="tab-bookings">
      <div class="table-card">
        <div class="table-header">
          <h3>📋 All Bookings ({{ total_bookings }})</h3>
          <input class="search-input" type="text" placeholder="🔍 Search bookings..." oninput="filterTable(this,'bookings-tbody')">
        </div>
        <table>
          <thead>
            <tr>
              <th>#</th><th>Guest Name</th><th>Email</th><th>Hotel</th>
              <th>Room</th><th>Check-in</th><th>Check-out</th>
              <th>Guests</th><th>Ref Code</th><th>Action</th>
            </tr>
          </thead>
          <tbody id="bookings-tbody">
            {% if bookings %}
              {% for b in bookings %}
              <tr>
                <td style="color:rgba(255,255,255,.3)">{{ loop.index }}</td>
                <td style="font-weight:600;color:#fff">{{ b.guest_name or "—" }}</td>
                <td style="font-size:.8rem">{{ b.user }}</td>
                <td>{{ b.hotel }}</td>
                <td><span class="badge badge-city">{{ b.room_type or "—" }}</span></td>
                <td>{{ b.check_in }}</td>
                <td>{{ b.check_out }}</td>
                <td>{{ b.guests }}</td>
                <td><span class="badge badge-ref">{{ b.ref_code }}</span></td>
                <td>
                  <form method="POST" action="/admin/delete-booking/{{ b.id }}" onsubmit="return confirm('Delete booking {{ b.ref_code }}?')">
                    <button class="btn-del">🗑 Delete</button>
                  </form>
                </td>
              </tr>
              {% endfor %}
            {% else %}
              <tr class="empty-row"><td colspan="10">No bookings found.</td></tr>
            {% endif %}
          </tbody>
        </table>
      </div>
    </div>

    <!-- USERS TAB -->
    <div id="tab-users" style="display:none">
      <div class="table-card">
        <div class="table-header">
          <h3>👥 Registered Users ({{ total_users }})</h3>
          <input class="search-input" type="text" placeholder="🔍 Search users..." oninput="filterTable(this,'users-tbody')">
        </div>
        <table>
          <thead>
            <tr><th>#</th><th>Name</th><th>Email</th><th>Action</th></tr>
          </thead>
          <tbody id="users-tbody">
            {% if users %}
              {% for u in users %}
              <tr>
                <td style="color:rgba(255,255,255,.3)">{{ loop.index }}</td>
                <td style="font-weight:600;color:#fff">{{ u.name or "—" }}</td>
                <td>{{ u.email }}</td>
                <td>
                  <form method="POST" action="/admin/delete-user/{{ u.id }}" onsubmit="return confirm('Delete user {{ u.email }} and all their bookings?')">
                    <button class="btn-del">🗑 Delete</button>
                  </form>
                </td>
              </tr>
              {% endfor %}
            {% else %}
              <tr class="empty-row"><td colspan="4">No users found.</td></tr>
            {% endif %}
          </tbody>
        </table>
      </div>
    </div>

    <!-- ANALYTICS TAB -->
    <div id="tab-analytics" style="display:none">
      <div class="table-card">
        <div class="table-header">
          <h3>📊 Bookings by Hotel</h3>
        </div>
        <div style="padding:24px">
          {% if hotel_stats %}
            {% set max_cnt = hotel_stats[0].cnt %}
            <div class="chart-wrap">
              {% for row in hotel_stats %}
              <div class="bar-row">
                <div class="bar-label" title="{{ row.hotel }}">{{ row.hotel }}</div>
                <div class="bar-track">
                  <div class="bar-fill" style="width:{{ (row.cnt / max_cnt * 100)|int }}%"></div>
                </div>
                <div class="bar-count">{{ row.cnt }}</div>
              </div>
              {% endfor %}
            </div>
          {% else %}
            <p style="color:rgba(255,255,255,.3);text-align:center;padding:40px">No booking data yet.</p>
          {% endif %}
        </div>
      </div>
    </div>

  </div>
</div>

<script>
const titles = {bookings:"All Bookings", users:"Users", analytics:"Analytics"};
function showTab(name) {
  ["bookings","users","analytics"].forEach(t => {
    document.getElementById("tab-"+t).style.display = t===name ? "block" : "none";
  });
  document.getElementById("page-title").textContent = titles[name];
  document.querySelectorAll(".nav-item").forEach((el,i) => el.classList.remove("active"));
  event.currentTarget.classList.add("active");
}
function filterTable(input, tbodyId) {
  const q = input.value.toLowerCase();
  document.querySelectorAll("#"+tbodyId+" tr").forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(q) ? "" : "none";
  });
}
</script>
</body>
</html>'''

with open('templates/admin_dashboard.html','w',encoding='utf-8') as f:
    f.write(html)
print('Admin dashboard written OK')
