python manage.py migrate app_folder zero
python manage.py migrate zero
python manage.py makemigrations app_folder --no-input 
python manage.py migrate --no-input
python manage.py runserver 0.0.0.0:8000
