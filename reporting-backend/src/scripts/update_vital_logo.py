import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

# --- Database Setup (Simplified for Script) ---
# Using the provided connection string
DATABASE_URL = "postgresql://postgres:ZINQrdsRJEQeYMsLEPazJJbyztwWSMiY@nozomi.proxy.rlwy.net:45435/railway"

# Define the base for declarative models
Base = declarative_base()

# Define the Organization model (simplified)
class Organization(Base):
    __tablename__ = "organization"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    logo_url = Column(String)

# --- Script Logic ---
def update_vital_logo():
    print(f"Connecting to database...")
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        
        VITAL_ORG_ID = 6
        CORRECT_LOGO_URL = "https://files.manuscdn.com/user_upload_by_module/session_file/112395888/jVmFovGFupJrOxNP.png"
        
        # Find the organization
        vital_org = db.query(Organization).filter(Organization.id == VITAL_ORG_ID).first()
        
        if vital_org:
            print(f"Found organization: {vital_org.name} (ID: {vital_org.id})")
            print(f"Current logo_url: {vital_org.logo_url}")
            
            # Update the logo URL
            vital_org.logo_url = CORRECT_LOGO_URL
            db.commit()
            
            print(f"Successfully updated logo_url to: {CORRECT_LOGO_URL}")
        else:
            print(f"Error: Organization with ID {VITAL_ORG_ID} not found.")
            
    except Exception as e:
        print(f"An error occurred during database operation: {e}")
        sys.exit(1)
    finally:
        if 'db' in locals() and db:
            db.close()

if __name__ == "__main__":
    update_vital_logo()
