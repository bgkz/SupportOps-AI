"""Start from the project root with python -m backend.worker."""

import argparse
import sys

from rq import SimpleWorker, Worker
from rq.timeouts import TimerDeathPenalty

from backend.queue import job, redis_connection


class WindowsWorker(SimpleWorker):
    death_penalty_class = TimerDeathPenalty


def main() -> None:
    parser = argparse.ArgumentParser(description="Process background jobs")
    parser.add_argument("--burst", action="store_true", help="Exit when queue is empty")
    args = parser.parse_args()
    worker_class = WindowsWorker if sys.platform == "win32" else Worker
    worker = worker_class([job], connection=redis_connection)
    worker.work(burst=args.burst)


if __name__ == "__main__":
    main()
