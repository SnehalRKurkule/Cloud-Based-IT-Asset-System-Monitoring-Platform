import os
import platform
import socket
import time

import psutil
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:5000")
INTERVAL = int(os.getenv("AGENT_INTERVAL", "10"))


def get_local_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "127.0.0.1"


def collect_metrics():
    return {
        "hostname": socket.gethostname(),
        "cpu_usage": round(psutil.cpu_percent(interval=1), 2),
        "memory_usage": round(psutil.virtual_memory().percent, 2),
        "disk_usage": round(psutil.disk_usage("/").percent, 2),
        "uptime_seconds": int(time.time() - psutil.boot_time())
    }


def register_asset():
    payload = {
        "hostname": socket.gethostname(),
        "ip_address": get_local_ip(),
        "os": f"{platform.system()} {platform.release()}",
        "asset_type": "Linux Server",
        "location": "Local"
    }

    response = requests.post(
        f"{API_URL}/api/assets/register",
        json=payload,
        timeout=5
    )
    response.raise_for_status()


def send_metrics(metrics):
    response = requests.post(
        f"{API_URL}/api/metrics",
        json=metrics,
        timeout=5
    )
    response.raise_for_status()
    return response.json()


def main():
    print("====================================")
    print(" IT System Monitoring Agent")
    print("====================================")
    print(f"API: {API_URL}")
    print(f"Interval: {INTERVAL} seconds")

    try:
        register_asset()
        print("Asset registration successful.")
    except Exception as exc:
        print(f"Initial registration failed: {exc}")

    while True:
        try:
            metrics = collect_metrics()
            result = send_metrics(metrics)

            print(
                f"CPU: {metrics['cpu_usage']:>5.1f}% | "
                f"RAM: {metrics['memory_usage']:>5.1f}% | "
                f"Disk: {metrics['disk_usage']:>5.1f}% | "
                f"Status: {result['status']}"
            )

        except requests.RequestException as exc:
            print(f"API connection error: {exc}")
        except Exception as exc:
            print(f"Agent error: {exc}")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
