import os
import subprocess
import time
import signal
import sys
import argparse
import requests
import json
from loguru import logger

BASE_DIR = "/Users/hyunchanan/Documents/GitHub"
PYTHON_CMD = "/opt/homebrew/Caskroom/miniconda/base/bin/python3"
UVICORN_CMD = "/opt/homebrew/Caskroom/miniconda/base/bin/uvicorn"

modules = {
    "SG_proj_001": {"cmd": [UVICORN_CMD, "api.main:app", "--host", "0.0.0.0", "--port", "8001"], "cwd": "SG_proj_001"},
    "SG_proj_002": {"cmd": [UVICORN_CMD, "src.main:app", "--host", "0.0.0.0", "--port", "8002"], "cwd": "SG_proj_002"},
    "SG_proj_003": {"cmd": [UVICORN_CMD, "src.main:app", "--host", "0.0.0.0", "--port", "8003"], "cwd": "SG_proj_003"},
    "SG_proj_004": {"cmd": [UVICORN_CMD, "src.main:app", "--host", "0.0.0.0", "--port", "8004"], "cwd": "SG_proj_004"},
    "SG_proj_006": {"cmd": [UVICORN_CMD, "api:app", "--host", "0.0.0.0", "--port", "8506"], "cwd": "SG_proj_006"},
    "SG_proj_007": {"cmd": [UVICORN_CMD, "api:app", "--host", "0.0.0.0", "--port", "8007"], "cwd": "SG_proj_007"},
    "SG_proj_009": {"cmd": [UVICORN_CMD, "api:app", "--host", "0.0.0.0", "--port", "8009"], "cwd": "SG_proj_009"},
    "SG_proj_010": {"cmd": [UVICORN_CMD, "src.main:app", "--host", "0.0.0.0", "--port", "8010"], "cwd": "SG_proj_010"},
    "SG_proj_011": {"cmd": [UVICORN_CMD, "src.main:app", "--host", "0.0.0.0", "--port", "8011"], "cwd": "SG_proj_011"},
    "SG_proj_012": {"cmd": [UVICORN_CMD, "src.main:app", "--host", "0.0.0.0", "--port", "8012"], "cwd": "SG_proj_012"},
    "SG_proj_013": {"cmd": [UVICORN_CMD, "src.main:app", "--host", "0.0.0.0", "--port", "8013"], "cwd": "SG_proj_013"},
    "SG_proj_014": {"cmd": [UVICORN_CMD, "src.main:app", "--host", "0.0.0.0", "--port", "8024"], "cwd": "SG_proj_014"},
}

processes = []

def cleanup(signum, frame):
    print("\n[CLI Operator] Cleaning up processes...")
    for p in processes:
        p.terminate()
    sys.exit(0)

def start_services():
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    env = os.environ.copy()
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    # Local environment overrides
    for i in [1,2,3,4,6,7,9,10,11,12,13]:
        port = 8506 if i == 6 else 8000 + i
        env[f"MODULE_{i:03d}_URL"] = f"http://127.0.0.1:{port}"
    env["MODULE_014_URL"] = "http://127.0.0.1:8024"

    logger.info("Starting local orchestrator and all backend modules...")
    for name, config in modules.items():
        cwd = os.path.join(BASE_DIR, config["cwd"])
        env["PYTHONPATH"] = cwd
        p = subprocess.Popen(config["cmd"], cwd=cwd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        processes.append(p)
        logger.info(f"Started {name} (PID: {p.pid})")

    logger.success("All modules started. Running in background. Press Ctrl+C to stop.")
    while True:
        time.sleep(1)

def run_test():
    url = "http://localhost:8024/orchestrate"
    # Default payload example
    payload = {
        "analysis_type": "physical",
        "metal_surface_image_path": "/Users/hyunchanan/Documents/GitHub/SG_proj_015/SG_sample_images/press_example.jpg",
        "target_specs": {
            "adhesion": 1000.0,
            "viscosity": 5000.0,
            "tg": -10.0,
            "processability_level": 3
        }
    }
    
    logger.info(f"Sending E2E test request to {url}")
    try:
        response = requests.post(url, json=payload, timeout=30.0)
        response.raise_for_status()
        logger.success("Orchestrator responded successfully!")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except requests.exceptions.RequestException as e:
        logger.error(f"E2E test failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SG Project 015 - CLI Operator (Control Tower)")
    parser.add_argument("action", choices=["start-all", "test-e2e"], help="Action to perform")
    
    args = parser.parse_args()
    
    if args.action == "start-all":
        start_services()
    elif args.action == "test-e2e":
        run_test()
