"""
Simple autoscaler that:
- polls Prometheus for average request latency (or uses a metric)
- scales Docker service by calling Docker API (through docker SDK)

This is intentionally simple for demo. Customize thresholds for your needs.
"""
import os
import time
import requests
from docker import DockerClient

PROM_URL = os.environ.get('PROMETHEUS_URL', 'http://prometheus:9090')
TARGET_SERVICE = os.environ.get('TARGET_SERVICE', 'autoscaler_playground_api')
POLL = int(os.environ.get('POLL_INTERVAL', '10'))

# thresholds (seconds)
SCALE_UP_LATENCY = float(os.environ.get('SCALE_UP_LATENCY', '0.12'))
SCALE_DOWN_LATENCY = float(os.environ.get('SCALE_DOWN_LATENCY', '0.06'))
MIN_REPLICAS = int(os.environ.get('MIN_REPLICAS', '1'))
MAX_REPLICAS = int(os.environ.get('MAX_REPLICAS', '6'))

client = DockerClient(base_url='unix://var/run/docker.sock')

def query_prom_latency():
    # this example queries histogram mean using promQL for the api_request_latency_seconds
    q = 'histogram_quantile(0.5, sum(rate(api_request_latency_seconds_bucket[1m])) by (le))'
    try:
        r = requests.get(f"{PROM_URL}/api/v1/query", params={'query': q}, timeout=5)
        data = r.json()
        value = float(data['data']['result'][0]['value'][1]) if data['data']['result'] else 0.0
        return value
    except Exception as e:
        print('prom query err', e)
        return 0.0


def get_current_replicas(service_name):
    # We rely on containers named by image; this is simple: count running containers with the image name prefix
    try:
        conts = client.containers.list(filters={"ancestor": service_name})
        return len(conts)
    except Exception as e:
        print('docker list err', e)
        return 0


def scale_to(target):
    # naive scaler: start/stop containers
    cur = get_current_replicas(TARGET_SERVICE)
    print(f"Scaling from {cur} -> {target}")
    if target == cur:
        return
    if target > cur:
        for i in range(target - cur):
            client.containers.run(TARGET_SERVICE, detach=True, network='playground')
    else:
        # stop arbitrary containers of the image
        conts = client.containers.list(filters={"ancestor": TARGET_SERVICE})
        to_stop = conts[:cur-target]
        for c in to_stop:
            c.stop()
            c.remove()


if __name__ == '__main__':
    print('autoscaler started')
    # ensure at least MIN_REPLICAS
    cur = get_current_replicas(TARGET_SERVICE)
    if cur < MIN_REPLICAS:
        scale_to(MIN_REPLICAS)

    while True:
        lat = query_prom_latency()
        print('latency', lat)
        cur = get_current_replicas(TARGET_SERVICE)
        if lat > SCALE_UP_LATENCY and cur < MAX_REPLICAS:
            scale_to(min(cur + 1, MAX_REPLICAS))
        elif lat < SCALE_DOWN_LATENCY and cur > MIN_REPLICAS:
            scale_to(max(cur - 1, MIN_REPLICAS))
        time.sleep(POLL)