"""
Backward compatibility shim.
Allows Docker to continue running: uvicorn api:app --host 0.0.0.0 --port 8000
The actual application lives in api/app.py.
"""
from api.app import app
