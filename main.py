"""
Smart Attendance — Single-file Flask dashboard
Save this as: smart_attendance_flask_app.py

Features:
- Auto-opens dashboard in browser
- Web dashboard UI (HTML + CSS)
- Buttons: Register Student, Train Model, Start Attendance
- View Attendance + Date Filter + Export Excel
- Calls: add_faces.py, train_model.py, attendance_module.py
"""

from flask import Flask, request, jsonify, send_file, render_template_string, redirect, url_for
import subprocess
import pandas as pd
import os
import io
from datetime import datetime

# ---- AUTO OPEN BROWSER ----
import webbrowser
from threading import Timer

app = Flask(__name__)

# Path to your scripts
ADD_FACES_SCRIPT = "add_faces.py"
TRAIN_MODEL_SCRIPT = "train_model.py"
ATTENDANCE_SCRIPT = "attendance_module.py"
ATTENDANCE_CSV = "attendance.csv"

# ---------------------------------------------------------------------------
# HTML TEMPLATE
# ---------------------------------------------------------------------------

INDEX_HTML = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Smart Attendance Dashboard</title>
  <style>
    :root{--bg:#f6f8fa;--card:#fff;--accent:#1976d2;--accent-dark:#1565c0;--danger:#d32f2f;--muted:#666}
    body{font-family:Inter,Segoe UI,Helvetica,Arial,sans-serif;background:var(--bg);margin:0;padding:30px;color:#222}
    .container{max-width:980px;margin:0 auto}
    .header{display:flex;align-items:center;justify-content:space-between}
    h1{font-size:20px;margin:0}
    .grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-top:20px}
    .btn{display:inline-block;padding:12px 18px;border-radius:10px;border:none;background:var(--accent);color:#fff;font-weight:600;text-decoration:none;cursor:pointer;text-align:center}
    .btn-danger{background:var(--danger)}
    .card{background:var(--card);padding:16px;border-radius:12px;box-shadow:0 6px 20px rgba(20,30,50,0.06)}
    .muted{color:var(--muted);font-size:13px}
    table{width:100%;border-collapse:collapse;margin-top:12px}
    th,td{padding:8px 6px;border-bottom:1px solid #eee;text-align:left}
    .controls{display:flex;gap:8px;align-items:center}
    input[type=date]{padding:8px;border-radius:8px;border:1px solid #ddd}
    .small{font-size:13px}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>SMART ATTENDANCE DASHBOARD</h1>
      <div class="muted">Server time: {{ server_time }}</div>
    </div>

    <div class="grid">
      <div class="card">
        <div style="display:flex;flex-direction:column;gap:10px">
          <button class="btn" onclick="action('register')">Register Student</button>
          <button class="btn" onclick="action('train')">Train Model</button>
          <button class="btn" onclick="action('start')">Start Attendance</button>
          <button class="btn" onclick="loadAttendance()">View Attendance</button>
          <button class="btn" onclick="exportExcel()">Export to Excel</button>
          <a class="btn btn-danger" href="/quit" onclick="return confirm('Quit server?')">Quit Server</a>
        </div>
      </div>

      <div class="card">
        <div class="controls">
          <label class="small">Filter date:</label>
          <input id="filter-date" type="date" />
          <button class="btn small" onclick="filterByDate()">Filter</button>
          <button class="btn small" onclick="clearFilter()">Clear</button>
        </div>
        <div id="status" class="muted small" style="margin-top:10px">Status: idle</div>
      </div>
    </div>

    <div id="table-wrap" class="card" style="margin-top:18px">
      <h3 style="margin-top:0">Attendance Records</h3>
      <div id="table-container">No data loaded. Click "View Attendance".</div>
    </div>

  </div>

<script>
async function action(name){
  setStatus('running '+name+'...');
  const res = await fetch('/api/action', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({action:name})
  });
  const j = await res.json();
  setStatus(j.message||'done');
  if(j.reload) loadAttendance();
}

function setStatus(t){ document.getElementById('status').innerText = 'Status: '+t }

async function loadAttendance(){
  setStatus('loading attendance...');
  const res = await fetch('/api/attendance');
  const j = await res.json();
  setStatus('loaded '+j.rows.length+' rows');
  renderTable(j.columns, j.rows);
}

function renderTable(columns, rows){
  if(rows.length===0){
    document.getElementById('table-container').innerHTML = '<div class="muted">No records found</div>';
    return
  }
  let html = '<table><thead><tr>' + columns.map(c=>'<th>'+c+'</th>').join('') + '</tr></thead><tbody>'
  + rows.map(r=>'<tr>'+r.map(cell=>'<td>'+cell+'</td>').join('')+'</tr>').join('') + '</tbody></table>'
  document.getElementById('table-container').innerHTML = html;
}

async function filterByDate(){
  const d = document.getElementById('filter-date').value;
  if(!d){ alert('Pick a date'); return }
  setStatus('filtering '+d);
  const res = await fetch('/api/attendance?date='+encodeURIComponent(d));
  const j = await res.json();
  setStatus('loaded '+j.rows.length+' rows');
  renderTable(j.columns,j.rows);
}

function clearFilter(){
  document.getElementById('filter-date').value='';
  loadAttendance();
}

async function exportExcel(){
  setStatus('exporting...');
  const res = await fetch('/api/export');
  if(res.status===200){
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'attendance_export.xlsx'; a.click();
    window.URL.revokeObjectURL(url);
    setStatus('export ready');
  } 
  else {
    const j = await res.json(); 
    setStatus('error: '+(j.error||res.status));
  }
}
</script>
</body>
</html>
'''

# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    server_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template_string(INDEX_HTML, server_time=server_time)


@app.route('/api/action', methods=['POST'])
def api_action():
    data = request.get_json() or {}
    action = data.get('action')

    if action == 'register':
        try:
            subprocess.run(["python", ADD_FACES_SCRIPT], check=True)
            return jsonify({'message':'Register script finished'})
        except subprocess.CalledProcessError as e:
            return jsonify({'message':str(e)}), 500

    if action == 'train':
        try:
            subprocess.run(["python", TRAIN_MODEL_SCRIPT], check=True)
            return jsonify({'message':'Training finished'})
        except subprocess.CalledProcessError as e:
            return jsonify({'message':str(e)}), 500

    if action == 'start':
        try:
            subprocess.run(["python", ATTENDANCE_SCRIPT], check=True)
            return jsonify({'message':'Attendance finished','reload':True})
        except subprocess.CalledProcessError as e:
            return jsonify({'message':str(e)}), 500

    return jsonify({'message':'Unknown action'}), 400


@app.route('/api/attendance')
def api_attendance():
    date = request.args.get('date')
    if not os.path.exists(ATTENDANCE_CSV):
        return jsonify({'columns':[], 'rows':[]})

    df = pd.read_csv(ATTENDANCE_CSV)

    if date:
        df = df[df.get('Date') == date]

    return jsonify({
        'columns': list(df.columns),
        'rows': df.fillna('').astype(str).values.tolist()
    })


@app.route('/api/export')
def api_export():
    if not os.path.exists(ATTENDANCE_CSV):
        return jsonify({'error':'attendance.csv not found'}), 404

    df = pd.read_csv(ATTENDANCE_CSV)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Attendance')

    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name='attendance_export.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/quit')
def quit_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
        return 'Server shutting down...'
    return 'Unable to shutdown server', 500


# ---------------------------------------------------------------------------
# AUTO-OPEN BROWSER + START SERVER
# ---------------------------------------------------------------------------

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(debug=True)
