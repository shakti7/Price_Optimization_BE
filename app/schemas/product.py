from pydantic import BaseModel, Field, confloat, validator
from typing import Optional,Dict, Any
from datetime import datetime


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Product name is required and should be within 100 characters.")
    description: Optional[str] = Field(None, max_length=500, description="Optional product description (max 500 characters).")
    cost_price: float = Field(..., gt=0, description="Cost price must be greater than 0.")
    selling_price: float = Field(..., gt=0, description="Selling price must be greater than 0.")
    category: str = Field(..., min_length=1, max_length=25, description="Category is required and must be within 25 characters.")
    stock_available: int = Field(..., ge=0, description="Stock available must be 0 or more.")
    units_sold: int = Field(..., ge=0, description="Units sold must be 0 or more.")

    @validator("units_sold")
    def check_stock(cls, units_sold, values):
        """Ensures that stock_available >= units_sold."""
        stock_available = values.get("stock_available")
        if stock_available is not None and units_sold > stock_available:
            raise ValueError("Units sold cannot be greater than stock available.")
        return units_sold


class ProductResponse(ProductCreate):

    product_id: int
    customer_rating: float = Field(4.5, description="Default customer rating of 4.5.")
    demand_forecast: Optional[float] = Field(None, description="Auto-calculated demand forecast based on sales & price.")
    optimised_price: Optional[float] = Field(None, description="Auto-calculated optimized price based on demand & cost.")
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    cost_price: Optional[float] = Field(None, gt=0)
    selling_price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, max_length=25)
    stock_available: Optional[int] = Field(None, ge=0)
    units_sold: Optional[int] = Field(None, ge=0)

class ProductResponseBody(BaseModel):
    status_code: Optional[int]
    status: Optional[str]
    data: Optional[Dict[str, Any]] 
    message: Optional[str]