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

import webbrowser
from threading import Timer

app = Flask(__name__)
ADD_FACES_SCRIPT = "add_faces.py"
TRAIN_MODEL_SCRIPT = "train_model.py"
ATTENDANCE_SCRIPT = "attendance_module.py"
ATTENDANCE_CSV = "attendance.csv"

INDEX_HTML = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Smart Attendance Dashboard</title>
  <style>
body{
    margin:0;
    font-family:"Segoe UI",sans-serif;
    background:#eef2f7;
}

.container{
    display:flex;
    max-width:1200px;
    margin:auto;
}

/* Sidebar */

.sidebar{

    width:240px;
    min-height:100vh;
    background:#111827;
    padding:25px;
    color:white;

}

.sidebar h2{
    margin-bottom:40px;
}

.menu-btn{

    width:100%;
    padding:14px;
    margin:10px 0;

    border:none;
    border-radius:12px;

    background:#2563eb;
    color:white;

    font-size:15px;
    cursor:pointer;
}

.menu-btn:hover{

    background:#1d4ed8;

}

/* Main */

.main{

    flex:1;
    padding:30px;

}

.header{

display:flex;
justify-content:space-between;
align-items:center;

}

.stats{

display:grid;
grid-template-columns:repeat(3,1fr);
gap:20px;
margin-top:25px;

}

.stat-card{

background:white;
padding:25px;
border-radius:18px;

box-shadow:
0 10px 30px rgba(0,0,0,.08);

}

.stat-card h1{

color:#2563eb;

}

.card{

background:white;
border-radius:18px;
padding:25px;
margin-top:25px;

box-shadow:
0 10px 30px rgba(0,0,0,.08);

}

table{

width:100%;
border-collapse:collapse;

}

th{

background:#2563eb;
color:white;

}

td,th{

padding:14px;

}

tr:nth-child(even){

background:#f1f5f9;

}
  </style>
</head>
<body>
  <div class="container">
    <aside class="sidebar">
      <h2>Smart Attendance</h2>
      <button class="menu-btn" onclick="openRegister()">👨‍🎓 Register Student</button>
      <button class="menu-btn" onclick="action('train')">🧠 Train Model</button>
      <button class="menu-btn" onclick="action('start')">📷 Start Attendance</button>
      <button class="menu-btn" onclick="loadAttendance()">📊 View Attendance</button>
    </aside>

    <main class="main">
      <div id="registerBox" style="display:none;position:fixed;inset:0;background:rgba(15,23,42,0.75);display:flex;align-items:center;justify-content:center;z-index:50;">
        <div style="background:white;border-radius:18px;padding:30px;width:min(420px,90%);box-shadow:0 20px 50px rgba(0,0,0,0.2);">
          <h2 style="margin-top:0">Register Student</h2>
          <input id="studentName" type="text" placeholder="Student name" style="width:100%;padding:14px;border:1px solid #d1d5db;border-radius:12px;margin-bottom:18px;" />
          <button class="menu-btn" style="width:100%;padding:14px;margin:0 0 12px 0;" onclick="registerStudent()">Start Registration</button>
          <button class="menu-btn" style="width:100%;padding:14px;margin:0;background:#6b7280;" onclick="document.getElementById('registerBox').style.display='none'">Cancel</button>
        </div>
      </div>
      <div class="header">
        <div>
          <h1>SMART ATTENDANCE DASHBOARD</h1>
          <div style="color:#4b5563;margin-top:8px">Server time: {{ server_time }}</div>
        </div>
        <div style="color:#4b5563">Status: Online</div>
      </div>

      <div class="stats">
        <div class="stat-card">
          <h1>Total Students</h1>
          <p style="font-size:36px;margin:0">{{ total_students }}</p>
        </div>
        <div class="stat-card">
          <h1>Today's Attendance</h1>
          <p style="font-size:36px;margin:0">{{ today_count }}</p>
        </div>
        <div class="stat-card">
          <h1>Status</h1>
          <p style="font-size:36px;margin:0">Online</p>
        </div>
      </div>

      <section class="card">
        <h2 style="margin-top:0">Attendance Records</h2>
        <div class="card" style="padding:0;box-shadow:none;margin:0">
          <div class="controls" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:20px">
            <label style="font-weight:600;color:#374151">Filter date:</label>
            <input id="filter-date" type="date" style="padding:12px;border-radius:12px;border:1px solid #d1d5db;" />
            <button class="menu-btn" style="width:auto;padding:12px 18px;" onclick="filterByDate()">Filter</button>
            <button class="menu-btn" style="width:auto;padding:12px 18px;" onclick="clearFilter()">Clear</button>
          </div>
        </div>
        <div id="status" style="color:#6b7280;margin-bottom:20px">Status: idle</div>
        <div id="table-container">No data loaded. Click "View Attendance".</div>
      </section>
    </main>
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
    document.getElementById('table-container').innerHTML = '<div style="color:#6b7280">No records found</div>';
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

function openRegister(){

document.getElementById(
"registerBox"
).style.display="block";

}

function registerStudent(){
    let name = document.getElementById("studentName").value.trim();
    if(!name){
        alert('Please enter a student name.');
        return;
    }

    fetch("/register",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({name:name})
    })
    .then(r=>r.json())
    .then(data=>{
        alert(data.message);
        document.getElementById('registerBox').style.display='none';
        document.getElementById('studentName').value='';
    })
    .catch(err=>{
        alert('Failed to start registration.');
        console.error(err);
    });
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

@app.route('/')
def index():
    server_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    total_students = 0
    today_count = 0
    today = datetime.now().strftime('%Y-%m-%d')

    if os.path.exists(ATTENDANCE_CSV):
        try:
            df = pd.read_csv(ATTENDANCE_CSV)
            if 'Name' in df.columns:
                total_students = int(df['Name'].nunique())
            else:
                total_students = int(len(df))
            if 'Date' in df.columns:
                today_count = int(df[df['Date'] == today].shape[0])
        except pd.errors.EmptyDataError:
            pass

    return render_template_string(
        INDEX_HTML,
        server_time=server_time,
        total_students=total_students,
        today_count=today_count,
    )


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


@app.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    name = data["name"]

    subprocess.Popen(
        ["python", "add_faces.py", name]
    )

    return jsonify(
        {
        "message":
        f"Camera started for {name}"
        }
    )


@app.route('/api/attendance')
def api_attendance():
    date = request.args.get('date')
    if not os.path.exists(ATTENDANCE_CSV):
        return jsonify({'columns':[], 'rows':[]})

    try:
        df = pd.read_csv(ATTENDANCE_CSV)
    except pd.errors.EmptyDataError:
        return jsonify({'columns':[], 'rows':[]})

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

    try:
        df = pd.read_csv(ATTENDANCE_CSV)
    except pd.errors.EmptyDataError:
        return jsonify({'error':'attendance.csv is empty'}), 404

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

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(host="127.0.0.1", port=5000)
