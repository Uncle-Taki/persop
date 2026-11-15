#!/usr/bin/env python3
"""Read-only operator health snapshot; exit nonzero when an alert needs attention."""
import argparse
import json
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from backup import Deployment


def redis(deployment, *args):
    result = deployment.run('exec', '-T', 'redis', 'sh', '-c',
                            'export REDISCLI_AUTH="$REDIS_PASSWORD"; exec redis-cli --json "$@"',
                            'sh', *map(str, args), stdout=subprocess.PIPE)
    return json.loads(result.stdout)


def pairs(row):
    return dict(zip(row[::2], row[1::2]))


def alerts_for(metrics, limits):
    alerts = []
    for key, limit in limits.items():
        if metrics.get(key, 0) > limit:
            alerts.append(key)
    for key in ('api_ready', 'gateway_connected', 'worker_present', 'backup_recent'):
        if not metrics.get(key, False):
            alerts.append(key)
    return alerts


def collect(deployment, url, backup_manifest, max_backup_hours):
    metrics = {}
    headers = {'Authorization': 'Bearer ' + deployment.values['API_TOKEN']}
    with urllib.request.urlopen(urllib.request.Request(url.rstrip('/') + '/api/v1/telegram/status', headers=headers), timeout=10) as response:
        status = json.load(response)['data']
    metrics['gateway_connected'] = status.get('connected', False) and not status.get('authorization_required', True)
    # An authenticated DB-backed API read checks the same route the operator uses.
    with urllib.request.urlopen(urllib.request.Request(url.rstrip('/') + '/api/v1/products?limit=1', headers=headers), timeout=10) as response:
        metrics['api_ready'] = response.status == 200
    stream = deployment.values.get('REDIS_STREAM_KEY', 'perso:telegram:messages')
    groups = redis(deployment, 'XINFO', 'GROUPS', stream)
    metrics['pending_count'] = sum(pairs(group)['pending'] for group in groups)
    metrics['oldest_pending_seconds'] = 0
    for group in groups:
        oldest = redis(deployment, 'XPENDING', stream, pairs(group)['name'], '-', '+', '1')
        if oldest:
            metrics['oldest_pending_seconds'] = max(metrics['oldest_pending_seconds'], max(0, time.time() - int(oldest[0][0].split('-')[0]) / 1000))
    metrics['dead_letters'] = redis(deployment, 'XLEN', stream + ':dead')
    metrics['stream_entries'] = redis(deployment, 'XLEN', stream)
    cursor, worker_keys = '0', set()
    for _ in range(1000):
        cursor, keys = redis(deployment, 'SCAN', cursor, 'MATCH', stream + ':workers:*', 'COUNT', '100')
        worker_keys.update(keys)
        if str(cursor) == '0':
            break
    else:
        raise ValueError('Worker scan exceeded the bounded inspection budget')
    metrics['worker_present'] = bool(worker_keys)
    metrics['worker_heartbeats'] = len(worker_keys)
    disk = deployment.run('exec', '-T', 'redis', 'df', '-Pk', '/data', stdout=subprocess.PIPE).stdout.decode().splitlines()[-1].split()
    metrics['redis_disk_percent'] = int(disk[-2].rstrip('%'))
    metrics['outbox_failures'] = int(deployment.sql("SELECT count(*) FROM outbound_messages WHERE status='failed'"))
    metrics['outbox_oldest_seconds'] = float(deployment.sql("SELECT COALESCE(EXTRACT(EPOCH FROM now()-min(created_at)),0) FROM outbound_messages WHERE status IN('queued','sending','failed')"))
    metrics['backup_recent'] = False
    if backup_manifest:
        manifest = json.loads(backup_manifest.read_text())
        created = datetime.fromisoformat(manifest['created_at'])
        age = (datetime.now(timezone.utc) - created).total_seconds()
        metrics['backup_age_hours'] = round(age / 3600, 2)
        metrics['backup_recent'] = 0 <= age <= max_backup_hours * 3600 and manifest['project'] == deployment.project
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True)
    parser.add_argument('--env-file', type=Path, required=True)
    parser.add_argument('--url', required=True, help='Same-origin HTTP(S) endpoint; no embedded credentials')
    parser.add_argument('--backup-manifest', type=Path)
    parser.add_argument('--max-backup-hours', type=float, default=26)
    parser.add_argument('--max-pending-seconds', type=float, default=300)
    parser.add_argument('--max-pending', type=int, default=1000)
    parser.add_argument('--max-disk-percent', type=int, default=80)
    args = parser.parse_args()
    try:
        metrics = collect(Deployment(args.project, args.env_file), args.url, args.backup_manifest, args.max_backup_hours)
        limits = {'pending_count': args.max_pending, 'oldest_pending_seconds': args.max_pending_seconds,
                  'redis_disk_percent': args.max_disk_percent, 'dead_letters': 0, 'outbox_failures': 0,
                  'outbox_oldest_seconds': args.max_pending_seconds}
        alerts = alerts_for(metrics, limits)
        print(json.dumps({'status': 'attention' if alerts else 'healthy', 'alerts': alerts, 'metrics': metrics}, indent=2))
        raise SystemExit(1 if alerts else 0)
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError):
        print(json.dumps({'status': 'unavailable', 'alerts': ['monitor_collection_failed']}))
        raise SystemExit(2)


if __name__ == '__main__':
    main()
