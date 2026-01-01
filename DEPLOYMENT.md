# payvest: Production deployment instructions

## 1. Install dependencies

uv pip install -e .

## 2. Run Gunicorn server (recommended for production)

# Directly using Gunicorn
gunicorn --bind=0.0.0.0 --timeout 600 "app:create_app()"

# Or Gunicorn via uv
uv run gunicorn --config gunicorn.conf.py

## 3. Environment variables
- Set FLASK_ENV=production for production mode
- Optionally set HOST, PORT, WORKERS

## 4. Cloud deployment notes
- Azure, AWS, GCP, PythonAnywhere
- Ensure static files are served by a reverse proxy (nginx, Apache, etc.)
- For HTTPS, configure SSL at the proxy/load balancer layer

## 5. Health check
- Endpoint: /healthz
- Status: 200 OK if app is running

## 6. Scaling
- Adjust WORKERS flag or gunicorn.conf.py for concurrency

## 7. Logging
- Access and error logs are sent to stdout/stderr (container-friendly)

## 8. Security
- Do not run as root; use a dedicated user in production
- Set proper CORS, session, and secret key settings in Flask config

## 9. Static files
- Flask serves static files from /static/ for development
- For production, use a CDN or web server for /static/

## 10. Database
- This app is stateless; no database required

---

For more details, see Flask and Gunicorn documentation.
