"""
Create a staff user (doctor) for login.
Usage: python manage.py create_doctor email@example.com password [--first-name "Jane" --last-name "Doe"]
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Create a doctor (staff) user for MedLink login."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)
        parser.add_argument("password", type=str)
        parser.add_argument("--first-name", default="", type=str)
        parser.add_argument("--last-name", default="", type=str)

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        password = options["password"]
        first_name = (options.get("first_name") or "").strip()
        last_name = (options.get("last_name") or "").strip()

        if User.objects.filter(email__iexact=email).exists():
            self.stdout.write(self.style.WARNING(f"User with email {email} already exists."))
            return

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,
            is_active=True,
        )
        self.stdout.write(self.style.SUCCESS(f"Doctor created: {email} (id={user.pk})"))
