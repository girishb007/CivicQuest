"""Explicitly opt-in local synthetic load baseline; never use a live DSN."""
import asyncio
import json
import os
from pathlib import Path
import statistics
import time
from urllib.parse import urlsplit

import httpx
import psycopg

url = os.environ['CQ_LOAD_DATABASE_URL'].replace('postgresql+psycopg:', 'postgresql:')
if urlsplit(url).hostname not in {'127.0.0.1', 'localhost'} or 'restore_check' not in urlsplit(url).path:
    raise SystemExit('Use the isolated localhost restore_check database for this synthetic load drill')
with psycopg.connect(url) as db:
    db.execute("""INSERT INTO reports
        (id, created_at, reporter_id, report_type, category, title, description, location, address,
         status, visibility, verification, severity, demo)
        SELECT md5('cq-load-' || g)::uuid::text, now() - mod(g,86400) * interval '1 second',
          (SELECT id FROM users WHERE handle='maya_demo'), 'place', 'pothole',
          'Synthetic load fixture ' || g, 'Generated solely for performance testing',
          ST_SetSRID(ST_MakePoint(72.8 + mod(g,200)*0.0008, 18.95 + mod(g/200,500)*0.0006),4326)::geography,
          'SYNTHETIC LOAD DATA', 'open', 'public', 'unverified', 2, true
        FROM generate_series(1,100000) g ON CONFLICT (id) DO NOTHING""")
    db.execute('ANALYZE reports')
    count = db.execute('SELECT count(*) FROM reports').fetchone()[0]


async def benchmark():
    results = {'feed': [], 'map': []}
    failures = []
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8001', timeout=30,
                                 limits=httpx.Limits(max_connections=50,max_keepalive_connections=50)) as client:
        async def citizen(index):
            for iteration in range(6):
                kind = 'feed' if iteration % 2 == 0 else 'map'
                path = '/api/v1/feed/places' if kind == 'feed' else '/api/v1/explore?lat=19.076&lng=72.878&radius_m=5000'
                start = time.perf_counter()
                response = await client.get(path)
                elapsed = time.perf_counter() - start
                results[kind].append(elapsed)
                if response.status_code != 200:
                    failures.append({'status': response.status_code, 'kind': kind})
        await asyncio.gather(*(citizen(i) for i in range(50)))
    report = {'reports': count, 'concurrent_users':50, 'failures':failures,
              'measurements':{kind:{'requests':len(times),'p50_ms':round(statistics.median(times)*1000,2),
                                    'p95_ms':round(sorted(times)[int(.95*(len(times)-1))]*1000,2)}
                              for kind,times in results.items()}}
    Path('docs/validation/load-baseline.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

asyncio.run(benchmark())
