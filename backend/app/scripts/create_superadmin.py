from getpass import getpass

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import func, select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import AdminUser

email_adapter = TypeAdapter(EmailStr)


def prompt_email() -> str:
    while True:
        raw_email = input("Super-admin email: ").strip().lower()

        try:
            return str(email_adapter.validate_python(raw_email))
        except ValidationError:
            print("ERROR: enter a valid email address.")


def prompt_password() -> str:
    while True:
        password = getpass("Password: ")

        if len(password) < 12:
            print("ERROR: password must be at least 12 characters.")
            continue

        confirmation = getpass("Confirm password: ")

        if password != confirmation:
            print("ERROR: passwords do not match.")
            continue

        return password


def main() -> None:
    with SessionLocal() as db:
        admin_count = db.scalar(select(func.count()).select_from(AdminUser))

        if admin_count:
            existing_admin = db.scalar(select(AdminUser).order_by(AdminUser.id))

            email = existing_admin.email if existing_admin is not None else "unknown"

            raise SystemExit(
                "ERROR: a super-admin already exists "
                f"({email}). Only one super-admin is allowed."
            )

        email = prompt_email()

        existing_email = db.scalar(select(AdminUser).where(AdminUser.email == email))

        if existing_email is not None:
            raise SystemExit("ERROR: an admin with that email already exists.")

        password = prompt_password()

        admin = AdminUser(
            email=email,
            hashed_password=hash_password(password),
            is_active=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print()
        print("Super-admin created successfully.")
        print(f"ID: {admin.id}")
        print(f"Email: {admin.email}")
        print(f"Active: {admin.is_active}")


if __name__ == "__main__":
    main()
