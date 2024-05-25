source venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput
deactivate

echo "Build completed."
