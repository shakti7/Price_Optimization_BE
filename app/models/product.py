from sqlalchemy import Column, Integer, String, Float, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Product(Base):
    __tablename__ = "Product_Data"

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    cost_price = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)
    category = Column(String(25), nullable=False)
    stock_available = Column(Integer, default=0)
    units_sold = Column(Integer, default=0)
    customer_rating = Column(Float, nullable=True)  
    demand_forecast = Column(Float, nullable=True)
    optimised_price = Column(Float, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationship with User 
    user = relationship("User", back_populates="products")
