
import getpass
import re

from werkzeug.security import generate_password_hash
from database import (
    initialize_database,
    initialize_admin_table,
    get_admin_by_email,
    create_admin,
)

initialize_database()
initialize_admin_table()

email = input("Enter admin email: ").strip().lower()

if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
    print("Please enter a valid email address.")
    raise SystemExit(1)

if get_admin_by_email(email):
    print("An admin account with this email already exists.")
    raise SystemExit(1)

password = getpass.getpass("Create admin password (minimum 12 characters): ")
confirm = getpass.getpass("Confirm admin password: ")

if len(password) < 12:
    print("Password must contain at least 12 characters.")
    raise SystemExit(1)

if password != confirm:
    print("Passwords do not match.")
    raise SystemExit(1)

create_admin(email, generate_password_hash(password))
print("Admin account created successfully.")
