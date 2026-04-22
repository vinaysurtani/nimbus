#!/usr/bin/env python3
import subprocess
import threading
import sys
import os

def run_fastapi():
    if sys.platform == "win32":
        python_cmd = "venv\\Scripts\\python"
    else:
        python_cmd = "venv/bin/python"
    
    subprocess.run([python_cmd, "main.py"])

def run_grpc():
    if sys.platform == "win32":
        python_cmd = "venv\\Scripts\\python"
    else:
        python_cmd = "venv/bin/python"
    
    subprocess.run([python_cmd, "grpc_server.py"])

if __name__ == "__main__":
    print("Starting Text Service (FastAPI + gRPC)...")
    
    # Start FastAPI in a separate thread
    fastapi_thread = threading.Thread(target=run_fastapi)
    fastapi_thread.daemon = True
    fastapi_thread.start()
    
    # Start gRPC server
    run_grpc()