source venv/bin/activate
#!/bin/bash
# Path to your build script
./build.sh
# Starting the Django application with gunicorn
exec python manage.py runserver 0.0.0.0:8000
