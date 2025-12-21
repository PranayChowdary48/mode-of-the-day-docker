from flask import Flask, jsonify
from prometheus_client import Counter, Histogram, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import time

app = Flask(__name__)
REQUEST_COUNT = Counter('api_request_count', 'Total HTTP requests')
REQUEST_LATENCY = Histogram('api_request_latency_seconds', 'Latency in seconds')

@app.route('/')
def index():
    start = time.time()
    REQUEST_COUNT.inc()
    # simulate some variable load
    time.sleep(0.05)
    REQUEST_LATENCY.observe(time.time() - start)
    return jsonify({"status": "ok"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# Expose metrics at /metrics
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {'/metrics': make_wsgi_app()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)