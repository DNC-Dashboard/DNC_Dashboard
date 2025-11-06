FROM python:3.9

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .
# install python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# running migrations
RUN python manage.py migrate

# Create superuser and assign default profile role
RUN python manage.py shell << EOF
from django.contrib.auth.models import User
from projects.models import Profile  # 👈 replace 'your_app' with your real app name

username = "admin1"
password = "admin1"
email = "admin@example.com"

user, created = User.objects.get_or_create(username=username, defaults={'email': email})
if created:
    user.set_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print(f"Superuser '{username}' created.")
else:
    print(f"Superuser '{username}' already exists.")

# Create or update the Profile
profile, _ = Profile.objects.get_or_create(user=user, defaults={'role': 'STAFF'})
if profile.role != 'STAFF':
    profile.role = 'STAFF'
    profile.save()
    print(f"Profile for '{username}' set to STAFF.")
EOF


# gunicorn
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "config.wsgi"]
