source venv/bin/activate
#!/bin/bash
echo "Installing requirements..."
pip install -r requirements.txt
# Starting the Django application with gunicorn
exec python manage.py runserver 0.0.0.0:8000
