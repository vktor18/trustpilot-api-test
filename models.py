from sqlalchemy import Column, String, Integer, DateTime, Text, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TPReview(Base):
    __tablename__ = "tp_reviews"

    Review_Id = Column(String, primary_key=True, index=True)
    Reviewer_Name = Column(String, nullable=True)
    Review_Title = Column(String, nullable=True)
    Review_Rating = Column(Integer, nullable=True)
    Review_Content = Column(Text, nullable=True)
    Review_IP_Address = Column(String, nullable=True)
    Business_Id = Column(String, nullable=True, index=True)
    Business_Name = Column(String, nullable=True)
    Reviewer_Id = Column(String, nullable=True, index=True)
    Email_Address = Column(String, nullable=True)
    Reviewer_Country = Column(String, nullable=True)
    Review_Date = Column(DateTime, nullable=True, index=True)


# optional composite/index examples (uncomment if needed)
# Index("ix_business_review_date", TPReview.Business_Id, TPReview.Review_Date)
