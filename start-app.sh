source venv/bin/activate
#!/bin/bash
# Starting the Django application with gunicorn
exec python manage.py runserver 0.0.0.0:8000
