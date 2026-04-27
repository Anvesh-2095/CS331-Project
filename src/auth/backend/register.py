import uuid
import utils
from database import SessionLocal
import models

def create_admin():
    db = SessionLocal()
    
    # Check if admin already exists
    existing_admin = db.query(models.User).filter(models.User.email == "test@soar.local").first()
    if existing_admin:
        print("[*] Admin already exists!")
        return

    # Create new admin
    new_admin = models.User(
        user_id=uuid.uuid4(),
        email="test@soar.local",
        password_hash=utils.get_password_hash("password"), # <--- Your new password
        full_name="System Administrator",
        role=models.UserRole.admin
    )
    
    db.add(new_admin)
    db.commit()
    print("[+] Admin user 'admin@soar.local' created successfully with password: adminpassword123")
    db.close()

if __name__ == "__main__":
    create_admin()