from sqlalchemy import Column, String, DateTime
from datetime import datetime
from database import Base

class PageToken(Base):
    __tablename__ = "page_tokens"

    page_id = Column(String, primary_key=True, index=True) # পেজের আইডি
    page_name = Column(String) # পেজের নাম
    access_token = Column(String) # আসল চাবি, এটা দিয়েই Reply যাবে
    created_at = Column(DateTime, default=datetime.utcnow)