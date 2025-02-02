from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate, ProductResponseBody
from app.core.auth_guard import get_current_user
from datetime import datetime
from typing import List
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/product",
    tags=["Product"]
)

def calculate_demand_forecast(units_sold: int, selling_price: float) -> float:
    if selling_price <= 0:
        return 0  

    base_demand = max(units_sold * 1.2, 10)  
    price_factor = 1 - (selling_price / 1000)  
    
    return round(base_demand * price_factor, 2)

def calculate_optimised_price(cost_price: float, selling_price: float, demand_forecast: float) -> float:

    profit_margin = (selling_price - cost_price) / cost_price if cost_price > 0 else 0
    price_adjustment = demand_forecast * 0.02  
    
    optimised_price = max(cost_price * (1 + profit_margin) + price_adjustment, cost_price)
    return round(optimised_price, 2)

@router.post("/add", response_model=ProductResponse)
def add_new_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    
    try:
        
        demand_forecast = calculate_demand_forecast(product_data.units_sold, product_data.selling_price)
        optimised_price = calculate_optimised_price(product_data.cost_price, product_data.selling_price, demand_forecast)

        
        new_product = Product(
            name=product_data.name,
            description=product_data.description,
            cost_price=product_data.cost_price,
            selling_price=product_data.selling_price,
            category=product_data.category,
            stock_available=product_data.stock_available,
            units_sold=product_data.units_sold,
            customer_rating=4.5,  # Default value
            demand_forecast=demand_forecast,
            optimised_price=optimised_price,
            user_id=current_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        return new_product

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/dashboard", response_model=List[ProductResponse])
def get_dashboard(
    page: int = Query(1, ge=1, description="Page number for pagination"),
    limit: int = Query(20, ge=1, le=50, description="Limit per page (max 50)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns all products for the logged-in user with pagination.
    """

    try:
        skip = (page - 1) * limit  # Calculate offset
        products = db.query(Product).filter(Product.user_id == current_user.id).offset(skip).limit(limit).all()

        if not products:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No products found for the user.")

        return products

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/delete/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    
    try:
        print("user_id: ",Product.user_id)
        product = db.query(Product).filter(Product.product_id == product_id, Product.user_id == current_user.id).first()

        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or unauthorized.")

        
        db.delete(product)
        db.commit()

        return {"message": "Product deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.patch("/update/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        
        product = db.query(Product).filter(Product.product_id == product_id, Product.user_id == current_user.id).first()
        print("ProductName: ",product)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or unauthorized.")

        
        update_fields = product_data.dict(exclude_unset=True)

        print("update_fields: ",update_fields)
        new_units_sold = update_fields.get("units_sold", product.units_sold)
        new_stock_available = update_fields.get("stock_available", product.stock_available)

        if "units_sold" in update_fields and "stock_available" in update_fields:
            if new_units_sold > new_stock_available:
                print("Yo")
                db.rollback() 
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Units sold cannot be greater than stock available.")
        elif "units_sold" in update_fields:  
            if new_units_sold > product.stock_available:
                db.rollback()  
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Units sold ({new_units_sold}) cannot exceed current stock available ({product.stock_available}).")

        
        if "units_sold" in update_fields or "selling_price" in update_fields:
            new_selling_price = update_fields.get("selling_price", product.selling_price)
            product.demand_forecast = calculate_demand_forecast(new_units_sold, new_selling_price)

        
        if "cost_price" in update_fields or "selling_price" in update_fields:
            new_cost_price = update_fields.get("cost_price", product.cost_price)
            new_selling_price = update_fields.get("selling_price", product.selling_price)
            product.optimised_price = calculate_optimised_price(new_cost_price, new_selling_price, product.demand_forecast)

        
        for field, value in update_fields.items():
            setattr(product, field, value)

        db.commit()  
        db.refresh(product)

        return product
        # # # Convert SQLAlchemy ORM Object to Dictionary
        # product["updated_at"] = datetime.utcnow().isoformat()
        # product["created_at"] = datetime.utcnow().isoformat()

        # response = ProductResponseBody(
        #     status_code=200,
        #     status="success",
        #     data=product,  
        #     message="Product updated successfully."
        # )
        
        # return JSONResponse(content=response.model_dump(mode="json"), status_code=200)




    except Exception as e:
        db.rollback()
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.get("/last-id", response_model=int)
def get_last_product_id(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    
    try:
        last_product = db.query(Product).order_by(Product.product_id.desc()).first()

        if not last_product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No products found for the user.")

        return last_product.product_id

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))