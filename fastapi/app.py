from main import app

# This file allows running with gunicorn as specified in CLAUDE.md:
# gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5002