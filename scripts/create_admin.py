from getpass import getpass

from app.core.database import SessionLocal, initialize_database
from app.schemas.admin import AdminCreate
from app.services.admin_service import create_admin


def main() -> None:
    initialize_database()
    admin_data = AdminCreate(
        name=input("Admin name: ").strip(),
        email=input("Admin email: ").strip(),
        password=getpass("Admin password: "),
    )
    with SessionLocal() as db:
        admin = create_admin(db, admin_data)
    print(f"Created admin account {admin.email} (id={admin.id}).")


if __name__ == "__main__":
    main()
