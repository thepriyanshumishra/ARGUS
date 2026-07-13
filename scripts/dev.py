import os
import signal
import subprocess
import sys
import threading
import time

# ANSI color codes for pretty printing
BLUE = "\033[94m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

processes = []
threads = []
should_exit = False


def log_stream(pipe, prefix, color):
    """Reads output from a pipe line by line and prints it with a prefix."""
    global should_exit
    try:
        with pipe:
            for line in iter(pipe.readline, b""):
                if should_exit:
                    break
                decoded_line = line.decode("utf-8", errors="replace").rstrip()
                # Print to stdout with prefix
                print(f"{color}{prefix}{RESET} {decoded_line}")
    except Exception as e:
        if not should_exit:
            print(f"{RED}[Dev Manager]{RESET} Error reading stream for {prefix}: {e}")


def signal_handler(sig, frame):
    """Gracefully handles shutdown when Ctrl+C or kill signals are received."""
    global should_exit
    if should_exit:
        return
    print(f"\n{RED}[Dev Manager]{RESET} Shutting down dev servers...")
    should_exit = True

    # Terminate all processes
    for p in processes:
        try:
            p.terminate()
        except ProcessLookupError:
            pass

    # Wait for processes to exit
    for p in processes:
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()

    sys.exit(0)


def start_process(command, cwd, prefix, color):
    """Starts a subprocess and spawns a thread to log its output."""
    try:
        import os
        env = os.environ.copy()
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        src_dir = os.path.join(root_dir, "src")
        existing_pythonpath = env.get("PYTHONPATH", "")
        if existing_pythonpath:
            env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{existing_pythonpath}"
        else:
            env["PYTHONPATH"] = src_dir

        p = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            env=env,
        )
        processes.append(p)

        # Start thread to log output
        t = threading.Thread(target=log_stream, args=(p.stdout, prefix, color), daemon=True)
        t.start()
        threads.append(t)
        return p
    except Exception as e:
        print(f"{RED}[Dev Manager]{RESET} Failed to start {prefix}: {e}")
        signal_handler(None, None)


def main():
    # Register shutdown signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_dir = os.path.join(root_dir, "frontend")

    # Locate virtual environment python if it exists
    venv_python = os.path.join(root_dir, ".venv", "bin", "python")
    if not os.path.exists(venv_python):
        venv_python = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
    python_exe = venv_python if os.path.exists(venv_python) else "python"

    print(f"{GREEN}[Dev Manager]{RESET} Using Python executable: {python_exe}")
    print(f"{GREEN}[Dev Manager]{RESET} Starting ARGUS Development Environment...")

    # Start Backend (FastAPI via uvicorn)
    print(f"{GREEN}[Dev Manager]{RESET} Starting FastAPI backend on http://localhost:8000")
    start_process(
        command=f"{python_exe} -m uvicorn argus.api.main:app --host 0.0.0.0 --port 8000 --reload",
        cwd=root_dir,
        prefix="[Backend]",
        color=GREEN,
    )

    # Give backend a moment to bind port before starting frontend
    time.sleep(1.5)

    # Start Frontend (Vite)
    print(f"{GREEN}[Dev Manager]{RESET} Starting Vite frontend on http://localhost:5173")
    start_process(
        command="npm run dev",
        cwd=frontend_dir,
        prefix="[Frontend]",
        color=BLUE,
    )

    # Keep main thread alive
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
