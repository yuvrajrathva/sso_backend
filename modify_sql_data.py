from sqlalchemy import MetaData, Table
from app.database import engine, SessionLocal

session = SessionLocal()

metadata = MetaData() 
metadata.reflect(bind=engine) 
verification_codes = Table('verification_codes', metadata, autoload_with=engine)
users = Table('users', metadata, autoload_with=engine)

def delete_verification_code(email):
    query = verification_codes.delete().where(verification_codes.c.email == email)
    session.execute(query)
    session.commit()
    print(f"Deleted verification code for email: {email}")

def delete_user(email):
    query = users.delete().where(users.c.email == email)
    session.execute(query)
    session.commit()
    print(f"Deleted user with email: {email}")

try:
    email = 'rathva.1@iitj.ac.in'

    # Delete from verification_codes
    print(f"Deleting from verification_codes for email: {email}")
    delete_verification_code(email)

    # Delete from users
    print(f"Deleting from users for email: {email}")
    delete_user(email)

except Exception as e:
    print(f"Error occurred: {e}")
finally:
    session.close()
    print("Database session closed")
