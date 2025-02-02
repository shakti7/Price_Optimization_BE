from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import text 
from app.routers import auth,profile, product
from app.core.database import get_db
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173"],  # Allow all origins (change this for security)
    allow_credentials=True,  # Allow sending cookies
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# @app.get("/test-db")
# def test_db_connection(db: Session = Depends(get_db)):
#     try:
#         db.execute(text("SELECT 1"))  # Simple query to check DB connection
#         return {"message": "Database connection successful!"}
#     except Exception as e:
#         return {"error": str(e)}

# Include authentication routes

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(product.router) 