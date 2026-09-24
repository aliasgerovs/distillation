#!/usr/bin/env bash
# Stop the replication queue and every job it started (frees all GPUs it holds).
# Restarting job_queue.py later skips passed jobs and reruns interrupted ones from scratch.
set -uo pipefail
cd "$(dirname "$0")/.."
pkill -f "replication/job_queue.py" && echo "queue stopped"
for m in replication/state/*.running; do
    [ -e "$m" ] || continue
    pid=$(cut -d' ' -f1 "$m")
    kill -- "-$pid" 2>/dev/null && echo "stopped $(basename "$m" .running) (pid $pid)"
    rm -f "$m"
done
echo "[$(date '+%Y-%m-%d %H:%M:%S')] queue and running jobs stopped with stop_queue.sh" >> replication/logs/queue.log
