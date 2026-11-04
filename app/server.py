"""Small local control plane for the persistent Bitburner browser agent."""
import asyncio
import gzip
import hashlib
import html
import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Optional

import httpx
from browser_use import Agent, BrowserProfile, BrowserSession, ChatOllama, Tools
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

STATE = Path(os.getenv("STATE_DIR", "/state"))
for name in ("profile", "checkpoints", "logs", "screenshots", "saves", "backups"):
    (STATE / name).mkdir(parents=True, exist_ok=True)
SAVE_DOWNLOADS = STATE / "saves"
SAVE_BACKUPS = STATE / "backups"
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bitburner-agent")
app = FastAPI(title="Bitburner AI OS", docs_url=None, redoc_url=None)
gate = asyncio.Lock()
runner: Optional[asyncio.Task] = None
backup_worker: Optional[asyncio.Task] = None
agent: Optional[Agent] = None
shared_browser: Optional[BrowserSession] = None
started_at = None
events: list[dict] = []
status = {"state": "stopped", "objective": "", "model": os.getenv("OLLAMA_MODEL", "unset"),
          "node": os.getenv("INFERENCE_NODE", "unconfigured"), "error": "", "steps": 0}
existing_events = STATE / "logs" / "actions.jsonl"
if existing_events.exists():
    try:
        events = [json.loads(line) for line in existing_events.read_text().splitlines()[-30:]]
    except Exception:
        log.exception("Could not load recent action events")


def record(kind: str, message: str) -> None:
    item = {"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "kind": kind, "message": str(message)[:1200]}
    events.append(item)
    del events[:-300]
    log_path = STATE / "logs" / "actions.jsonl"
    if log_path.exists() and log_path.stat().st_size > 1_000_000:
        for generation in (2, 1):
            src = log_path.with_suffix(f".jsonl.{generation}") if generation > 1 else log_path.with_suffix(".jsonl")
            dst = log_path.with_suffix(f".jsonl.{generation + 1}")
            if src.exists():
                shutil.move(src, dst)
        if log_path.exists():
            shutil.move(log_path, log_path.with_suffix(".jsonl.1"))
    with log_path.open("a") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def save_checkpoint(checkpoint: dict) -> None:
    path = STATE / "checkpoints" / "latest.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2))
    os.replace(temporary, path)


class StartRequest(BaseModel):
    objective: str = Field(min_length=3, max_length=2000)


def get_model() -> ChatOllama:
    base = os.environ["OLLAMA_BASE_URL"].rstrip("/")
    return ChatOllama(model=os.environ["OLLAMA_MODEL"], host=base, timeout=float(os.getenv("OLLAMA_TIMEOUT", "120")))


def get_browser_profile() -> BrowserProfile:
    domains = [d.strip() for d in os.getenv("ALLOWED_DOMAINS", "bitburner-official.github.io").split(",") if d.strip()]
    return BrowserProfile(user_data_dir=str(STATE / "profile"), headless=False, allowed_domains=domains,
                          downloads_path=str(STATE / "saves"), enable_default_extensions=False, keep_alive=True)


async def archive_game_saves() -> None:
    """Move completed native game exports into a separate, bounded backup directory."""
    retention = max(1, min(100, int(os.getenv("SAVE_BACKUP_RETENTION", "30"))))
    seen: dict[str, tuple[int, int]] = {}
    while True:
        try:
            for source in SAVE_DOWNLOADS.glob("*.json.gz"):
                backup = None
                signature = (0, 0)
                try:
                    stat = source.stat()
                    signature = (stat.st_size, stat.st_mtime_ns)
                    if stat.st_size <= 0 or stat.st_size > 50_000_000 or time.time() - stat.st_mtime < 20:
                        continue
                    if seen.get(source.name) != signature:
                        seen[source.name] = signature
                        continue
                    digest = hashlib.sha256()
                    with source.open("rb") as stream:
                        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                            digest.update(chunk)
                    backup = SAVE_BACKUPS / f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{digest.hexdigest()[:12]}.json.gz"
                    if backup.exists():
                        source.unlink(missing_ok=True)
                        continue
                    shutil.copy2(source, backup)
                    # Read the full compressed stream to check its gzip CRC before deleting the download.
                    with gzip.open(backup, "rb") as stream:
                        while stream.read(1024 * 1024):
                            pass
                    source.unlink(missing_ok=True)
                    record("backup", f"Archived native game save {backup.name} ({stat.st_size} bytes)")
                except (OSError, EOFError, gzip.BadGzipFile) as exc:
                    if backup is not None:
                        backup.unlink(missing_ok=True)
                    record("warning", f"Game-save archive skipped {source.name}: {type(exc).__name__}")
                    seen[source.name] = signature
            archives = sorted(SAVE_BACKUPS.glob("*.json.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
            for old in archives[retention:]:
                old.unlink(missing_ok=True)
        except Exception as exc:
            record("warning", f"Game-save backup watcher error: {type(exc).__name__}")
            log.exception("Game-save backup watcher failed")
        await asyncio.sleep(max(15, int(os.getenv("SAVE_BACKUP_SCAN_SECONDS", "30"))))


async def run_agent(objective: str) -> None:
    global agent, shared_browser
    status.update(state="running", objective=objective, error="", steps=0, node=os.getenv("INFERENCE_NODE", "unconfigured"))
    record("session", f"Started: {objective}")
    profile = get_browser_profile()
    if shared_browser is None:
        shared_browser = BrowserSession(browser_profile=profile)
    # These stock actions provide arbitrary code/file access; gameplay must use the UI and Netscript.
    tools = Tools(exclude_actions=["evaluate", "write_file", "replace_file", "read_file", "upload_file",
                                  "search", "search_page", "save_as_pdf", "run_python", "run_bash"])
    checkpoint_path = STATE / "checkpoints" / "latest.json"
    previous = json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else None
    progress = f"\nPrevious checkpoint (summary only): {json.dumps(previous, ensure_ascii=False)[:3500]}" if previous else ""
    task = f"Open {os.getenv('GAME_URL', 'https://bitburner-official.github.io/')} using ordinary visible browser controls. {objective}{progress}"
    last_activity = time.monotonic()

    async def on_step_start(current: Agent) -> None:
        nonlocal last_activity
        last_activity = time.monotonic()

    async def on_step_end(current: Agent) -> None:
        nonlocal last_activity
        last_activity = time.monotonic()
        status["steps"] += 1
        actions = []
        try:
            latest = current.history.history[-1]
            actions = [a.model_dump(exclude_none=True, mode="json") for a in latest.model_output.action]
        except Exception:
            pass
        record("action", f"Step {status['steps']}: {json.dumps(actions, ensure_ascii=False)[:700]}")
        save_checkpoint({"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                         "objective": objective, "session": status.get("session", 1),
                         "steps": status["steps"], "state": "in_progress",
                         "result": f"Completed visible browser action: {json.dumps(actions, ensure_ascii=False)[:1800]}"})
        if status["steps"] % 4 == 0:
            shot = STATE / "screenshots" / f"{int(time.time())}.png"
            try:
                await current.browser_session.take_screenshot(path=str(shot))
                images = sorted((STATE / "screenshots").glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
                for old in images[20:]:
                    old.unlink(missing_ok=True)
            except Exception as exc:
                record("warning", f"Screenshot capture failed: {type(exc).__name__}")

    agent = Agent(task=task, llm=get_model(), browser_profile=profile, browser_session=shared_browser, tools=tools,
                  use_vision=True, use_judge=False, max_failures=int(os.getenv("MAX_FAILURES", "2")),
                  max_actions_per_step=4, enable_signal_handler=False,
                  max_history_items=12,
                  save_conversation_path=STATE / "logs" / "conversation.json")
    try:
        run_task = asyncio.create_task(agent.run(max_steps=int(os.getenv("MAX_STEPS", "8")),
                                                 on_step_start=on_step_start, on_step_end=on_step_end))
        idle_limit = max(60, int(os.getenv("IDLE_TIMEOUT", "900")))
        while not run_task.done():
            try:
                await asyncio.wait_for(asyncio.shield(run_task), timeout=min(30, idle_limit))
            except asyncio.TimeoutError:
                if time.monotonic() - last_activity >= idle_limit:
                    agent.stop()
                    run_task.cancel()
                    await asyncio.gather(run_task, return_exceptions=True)
                    raise TimeoutError(f"No agent step completed for {idle_limit} seconds")
        history = await run_task
        status["steps"] = len(history.history)
        record("session", f"Completed {len(history.history)} steps")
        # Checkpoint is an objective/progress memo, never game state.
        checkpoint = {"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "objective": objective,
                      "steps": len(history.history), "result": str(history.final_result())[:3000]}
        checkpoint["state"] = "completed"
        save_checkpoint(checkpoint)
        record("checkpoint", checkpoint["result"] or "session ended")
    except asyncio.CancelledError:
        status.update(state="stopped")
        record("session", "Cancelled by operator")
        raise
    except Exception as exc:
        status.update(error=f"{type(exc).__name__}: {exc}")
        record("error", status["error"])
    finally:
        if status["state"] == "running":
            status["state"] = "stopped"
        agent = None


async def supervise(objective: str) -> None:
    """Run bounded, sequential sessions and stop on repeated failures or results."""
    (STATE / "checkpoints" / "objective.json").write_text(json.dumps({"objective": objective}, indent=2))
    maximum = max(1, min(24, int(os.getenv("MAX_SESSIONS", "12"))))
    retry_limit = max(1, min(4, int(os.getenv("MAX_RETRIES", "2"))))
    prior_result = ""
    repeats = 0
    failures = 0
    for number in range(1, maximum + 1):
        status.update(session=number, sessions_limit=maximum)
        await run_agent(objective)
        if status.get("error"):
            failures += 1
            if failures >= retry_limit:
                record("supervisor", f"Stopped after {failures} consecutive failed sessions")
                break
            await asyncio.sleep(min(30 * failures, 60))
            continue
        failures = 0
        checkpoint = STATE / "checkpoints" / "latest.json"
        result = json.loads(checkpoint.read_text()).get("result", "") if checkpoint.exists() else ""
        repeats = repeats + 1 if result and result == prior_result else 0
        prior_result = result
        if repeats >= 2:
            record("supervisor", "Stopped after repeated identical session results")
            break
        if number < maximum:
            await asyncio.sleep(max(10, min(600, int(os.getenv("SESSION_DELAY", "60")))))
    if status["state"] != "paused":
        status["state"] = "stopped"
        record("supervisor", f"Supervisor stopped after at most {maximum} sessions")


@app.get("/api/status")
async def get_status():
    checkpoint = STATE / "checkpoints" / "latest.json"
    return {**status, "events": events[-30:], "checkpoint": json.loads(checkpoint.read_text()) if checkpoint.exists() else None}


@app.get("/api/game-observation")
async def game_observation():
    """Expose only the rendered, model-visible game UI text, never game internals."""
    if shared_browser is None:
        return {"available": False, "message": "Start the player to open the game browser."}
    try:
        summary = await shared_browser.get_browser_state_summary(include_screenshot=False)
        text = summary.dom_state.llm_representation()
        current = {}
        for path, label in (("memory.current", "ram_used_bytes"), ("memory.max", "ram_limit_bytes")):
            try:
                current[label] = int(Path("/sys/fs/cgroup/" + path).read_text().strip())
            except (OSError, ValueError):
                current[label] = None
        return {"available": True, "url": summary.url, "title": summary.title,
                "visible_ui": text[:12000], "runtime": current,
                "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    except Exception as exc:
        raise HTTPException(503, f"Visible game observation unavailable: {type(exc).__name__}")


@app.get("/api/health")
async def health():
    return {"ok": True, "state": status["state"], "browser_ready": shared_browser is not None}


@app.get("/api/backups")
async def get_backups():
    archives = sorted(SAVE_BACKUPS.glob("*.json.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
    return {"count": len(archives), "retention": max(1, min(100, int(os.getenv("SAVE_BACKUP_RETENTION", "30")))),
            "backups": [{"name": p.name, "size_bytes": p.stat().st_size,
                         "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(p.stat().st_mtime))}
                        for p in archives]}


@app.post("/api/start")
async def start(req: StartRequest):
    global runner
    async with gate:
        if runner and not runner.done():
            raise HTTPException(409, "An agent session is already active")
        runner = asyncio.create_task(supervise(req.objective))
    return {"started": True}


@app.post("/api/pause")
async def pause():
    if status["state"] != "running" or not agent:
        raise HTTPException(409, "No active session")
    agent.pause()
    status["state"] = "paused"
    record("control", "Paused")
    return {"paused": True}


@app.post("/api/resume")
async def resume():
    if status["state"] != "paused" or not agent:
        raise HTTPException(409, "No paused session")
    agent.resume()
    status["state"] = "running"
    record("control", "Resumed")
    return {"resumed": True}


@app.post("/api/stop")
async def stop():
    if agent:
        agent.stop()
    if runner and not runner.done():
        runner.cancel()
    # An explicit emergency stop must survive a later service/VM restart.
    (STATE / "checkpoints" / "objective.json").unlink(missing_ok=True)
    status["state"] = "stopped"
    record("control", "Emergency stop")
    return {"stopped": True}


@app.post("/api/inference-check")
async def inference_check():
    base = os.environ["OLLAMA_BASE_URL"].rstrip("/")
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(base + "/api/tags")
            r.raise_for_status()
            models = [m["name"] for m in r.json().get("models", [])]
            return {"endpoint": base, "model": os.getenv("OLLAMA_MODEL"), "models": models,
                    "model_available": os.getenv("OLLAMA_MODEL") in models}
        except Exception as exc:
            raise HTTPException(502, f"Inference endpoint check failed: {type(exc).__name__}")


@app.on_event("startup")
async def auto_resume():
    global runner, shared_browser, backup_worker
    # Keep the actual game visible and ready for observation even while inference is idle.
    backup_worker = asyncio.create_task(archive_game_saves())
    try:
        shared_browser = BrowserSession(browser_profile=get_browser_profile())
        await shared_browser.start()
        await shared_browser.navigate_to(os.getenv("GAME_URL", "https://bitburner-official.github.io/"))
        record("browser", "Persistent game browser ready")
    except Exception as exc:
        shared_browser = None
        record("error", f"Browser startup failed: {type(exc).__name__}: {exc}")
        log.exception("Could not start persistent game browser")
    if os.getenv("AUTO_RESUME", "0") != "1":
        return
    objective_file = STATE / "checkpoints" / "objective.json"
    if objective_file.exists():
        try:
            objective = json.loads(objective_file.read_text())["objective"]
        except Exception:
            log.exception("Could not load saved objective; leaving player stopped")
            return
        runner = asyncio.create_task(supervise(objective))


@app.on_event("shutdown")
async def shutdown_tasks():
    if backup_worker and not backup_worker.done():
        backup_worker.cancel()
        await asyncio.gather(backup_worker, return_exceptions=True)
    if agent:
        agent.stop()


PAGE = r"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Bitburner AI OS</title>
<style>body{font:16px system-ui;background:#111827;color:#e5e7eb;max-width:1100px;margin:2rem auto;padding:0 1rem}section{background:#1f2937;padding:1rem;margin:1rem 0;border-radius:8px}button{padding:.6rem;margin:.3rem;background:#2563eb;color:white;border:0;border-radius:5px}textarea{width:98%;height:5rem;background:#111827;color:white}pre{white-space:pre-wrap;max-height:22rem;overflow:auto}.grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem}a{color:#93c5fd}</style>
<h1>Bitburner AI OS</h1><section><b id=s>Loading</b> · <span id=m></span><p>Viewer: <a href="http://localhost:6080/vnc.html?autoconnect=1&resize=scale&view_only=1" target=_blank>Read-only Chromium</a> · <button onclick="window.open('http://localhost:6080/vnc.html?autoconnect=1&resize=scale','_blank')">Open interactive viewer</button></p><textarea id=o>__DEFAULT_OBJECTIVE__</textarea><br><button onclick="post('/api/start',{objective:o.value})">Start</button><button onclick="post('/api/pause')">Pause</button><button onclick="post('/api/resume')">Resume</button><button onclick="post('/api/stop')">Emergency stop</button><button onclick="post('/api/inference-check')">Check inference</button></section>
<div class=grid><section><h2>Recent actions and errors</h2><pre id=e></pre></section><section><h2>Checkpoint</h2><pre id=c></pre></section></div><section><h2>Read-only game observation</h2><button onclick="refreshGame()">Refresh visible game stats</button><p>Values come from rendered game UI text and container resource limits; no game internals are read.</p><pre id=g>Open the player once to observe the game interface.</pre></section>
<section><h2>Verified game-save backups</h2><button onclick="refreshBackups()">Refresh backups</button><pre id=b>No game-native export archived yet.</pre></section>
<script>async function post(u,b={}){let r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});alert(await r.text());refresh()}async function refresh(){try{let x=await(await fetch('/api/status')).json();s.textContent=x.state.toUpperCase()+(x.error?' — '+x.error:'');m.textContent=x.model+' @ '+x.node;e.textContent=x.events.map(v=>v.time+' ['+v.kind+'] '+v.message).join('\n');c.textContent=JSON.stringify(x.checkpoint,null,2)||'No checkpoint yet'}catch{}}async function refreshGame(){g.textContent=JSON.stringify(await(await fetch('/api/game-observation')).json(),null,2)}async function refreshBackups(){try{let x=await(await fetch('/api/backups')).json();b.textContent=JSON.stringify(x,null,2)}catch{}}setInterval(refresh,2500);setInterval(refreshBackups,30000);refresh();refreshBackups()</script>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    objective_path = Path("/config/objective.md")
    objective = objective_path.read_text() if objective_path.exists() else "Learn Bitburner through visible game controls and documented Netscript, continuing from the last checkpoint."
    return PAGE.replace("__DEFAULT_OBJECTIVE__", html.escape(objective))
