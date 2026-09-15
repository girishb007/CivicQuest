"""Restart the prepared macOS local demo runtime (see docs/LOCAL_NATIVE.md)."""
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = Path.home() / "Library/Caches/CivicQuest"
PG = RUNTIME / "Postgres.app/Contents/Versions/16/bin"
PYTHON = RUNTIME / "api-env/bin/python"
NODE = shutil.which("node") or str(Path.home() / ".nvm/versions/node/v22.23.2/bin/node")
ENV = dict(os.environ, PYTHONPATH=str(ROOT / "apps/api"),
           CQ_DATABASE_URL="postgresql+psycopg://civicquest@127.0.0.1:55434/civicquest",
           CQ_MEDIA_ROOT=str(RUNTIME / "media"), CQ_QUEUE_MODE="database",
           CQ_ORIGIN="http://localhost:3000", CQ_ENV="local", CQ_DEMO_MODE="true",
           API_INTERNAL_URL="http://127.0.0.1:8001")


def listening(port):
    with socket.socket() as connection:
        return connection.connect_ex(("127.0.0.1", port)) == 0


def run(args):
    subprocess.run([str(a) for a in args], cwd=ROOT, env=ENV, check=True)


def sync_web():
    # Cloud placeholders can report stale sizes to rsync. Read to EOF and replace
    # each file atomically so Next never compiles a partially copied stylesheet.
    source = ROOT / "apps/web"
    destination = RUNTIME / "web"
    for folder, dirs, files in os.walk(source):
        dirs[:] = [d for d in dirs if d not in {"node_modules", ".next", ".git"}]
        for name in files:
            if name in {"tsconfig.tsbuildinfo", ".DS_Store"}:
                continue
            path = Path(folder) / name
            target = destination / path.relative_to(source)
            # Most files are unchanged between starts. Avoid reading both cloud-backed
            # trees when the last atomic sync is at least as new and has the same size.
            # Changed files still read to EOF below, which prevents partial Next inputs.
            if target.exists():
                source_stat = path.stat()
                target_stat = target.stat()
                if (
                    target_stat.st_size == source_stat.st_size
                    and target_stat.st_mtime_ns >= source_stat.st_mtime_ns
                ):
                    continue
            content = path.read_bytes()
            if target.exists() and target.read_bytes() == content:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".sync-tmp")
            temporary.write_bytes(content)
            temporary.replace(target)


def start(name, args, cwd, port=None):
    pidfile = RUNTIME / f"{name}.pid"
    if pidfile.exists():
        try:
            pid = int(pidfile.read_text())
            command = subprocess.check_output(["ps", "-p", str(pid), "-o", "command="], text=True)
            if " ".join(str(arg) for arg in args[1:]) in command:
                print(f"{name} already running ({pid})")
                return
        except (ProcessLookupError, ValueError, subprocess.CalledProcessError):
            pass
    if port and listening(port):
        raise SystemExit(f"Port {port} is occupied; inspect that service before restarting {name}.")
    with (RUNTIME / f"{name}.log").open("a") as log:
        process = subprocess.Popen([str(a) for a in args], cwd=cwd, env=ENV,
                                   stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                   start_new_session=True)
    pidfile.write_text(str(process.pid))
    time.sleep(1)
    if process.poll() is not None:
        raise SystemExit(f"{name} failed; see {RUNTIME / (name + '.log')}")
    print(f"Started {name} ({process.pid})")


if __name__ == "__main__":
    if not PYTHON.exists() or not (PG / "pg_ctl").exists():
        raise SystemExit("Prepare dependencies first; see docs/LOCAL_NATIVE.md")
    if not listening(55434):
        run([PG / "pg_ctl", "-D", RUNTIME / "pgdata", "-l", RUNTIME / "postgres.log",
             "-o", "-p 55434 -h 127.0.0.1 -k /private/tmp", "start"])
    run([PYTHON, "-m", "alembic", "upgrade", "head"])
    run([PYTHON, "-m", "civicquest.cli", "seed"])
    sync_web()
    start("api", [PYTHON, "-m", "uvicorn", "civicquest.main:app", "--host", "127.0.0.1",
                  "--port", "8001", "--no-access-log"], ROOT, 8001)
    start("worker", [PYTHON, "-m", "civicquest.cli", "worker"], ROOT)
    start("web", [NODE, "node_modules/next/dist/bin/next", "dev", "--webpack",
                  "--hostname", "127.0.0.1", "--port", "3000"], RUNTIME / "web", 3000)
    print("Open http://localhost:3000 (synthetic local demo). Logs:", RUNTIME)
