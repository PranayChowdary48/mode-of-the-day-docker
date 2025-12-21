import os
import time
import requests
import gevent
from gevent.pool import Pool

TARGET = os.environ.get('TARGET', 'http://proxy:80')
RPS = int(os.environ.get('RPS', '10'))
CONCURRENCY = int(os.environ.get('CONCURRENCY', '20'))

print(f"Starting load generator -> target={TARGET} rps={RPS} conc={CONCURRENCY}")

def do_request():
    try:
        r = requests.get(TARGET, timeout=5)
        # optional: print status
        # print(r.status_code)
    except Exception as e:
        print('req err', e)

if __name__ == '__main__':
    pool = Pool(CONCURRENCY)
    while True:
        jobs = []
        for _ in range(RPS):
            jobs.append(pool.spawn(do_request))
        gevent.joinall(jobs)
        time.sleep(1)