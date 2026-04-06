# dummy helper file to populate the database

from database import SessionLocal, engine
import models
import utils

# Ensure tables are created before we try to insert data
models.Base.metadata.create_all(bind=engine)

def seed_database():
    db = SessionLocal()
    try:
        # 1. Check if the database is already populated
        if db.query(models.User).count() > 0:
            print("[-] Users already exist in the database. Aborting.")
            return

        # 2. Create the Admin User
        admin = models.User(
            email="admin@soar.local",
            password_hash=utils.get_password_hash("admin123"),
            full_name="System Administrator",
            role=models.UserRole.admin
        )

        # 3. Create the Analyst User
        analyst = models.User(
            email="analyst@soar.local",
            password_hash=utils.get_password_hash("password123"),
            full_name="Security Analyst",
            role=models.UserRole.analyst
        )

        # 4. Save them to PostgreSQL
        db.add(admin)
        db.add(analyst)
        db.commit()
        
        print("[+] SUCCESS: Database seeded!")
        print("    -> Admin: admin@soar.local / admin123")
        print("    -> Analyst: analyst@soar.local / password123")
        
    except Exception as e:
        print(f"[-] Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()