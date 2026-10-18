# SupportOps AI

## Background jobs (Redis + RQ)

Run all commands from the project root in PowerShell.

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
docker compose --env-file backend/.env up -d redis
.\backend\.venv\Scripts\python.exe -m backend.worker
```

Keep the worker running in a separate terminal. Enqueue an importable function:

```python
from backend.queue import job
from backend.jobs.tickets import process_ticket  # Your own job module/function

queued_job = job.enqueue(process_ticket, str(ticket.id))
```

Create the job function in a regular Python module before using this example.
Pass IDs and simple values; open a new database session inside the job.
Enqueue only after committing the ticket transaction.

Optional settings in `backend/.env`:

```dotenv
REDIS_URL=redis://127.0.0.1:6379/0
RQ_QUEUE_NAME=default
```

Jobs have a default timeout of 300 seconds. Override with `job_timeout=600`
when enqueuing. Windows uses SimpleWorker with TimerDeathPenalty for local
development; Linux uses the standard RQ worker with process isolation.
Redis persists its data in the `redis_data` Docker volume.
