from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.db import SessionLocal
from app.models.product import Product
from app.schemas.product import ProductRead, ProductListResponse
from typing import List, Optional
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/products", tags=["products"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get(
    "/",
    response_model=ProductListResponse,
    summary="List Products",
    description="Returns a paginated list of available products as JSON. You can optionally filter by location (ISO code) using query params. Requires Authorization header."
)
def list_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    location: Optional[str] = Query(None, description="ISO code for country (e.g., JO, SA)")
):
    query = db.query(Product).options(joinedload(Product.country))
    if location and location.lower() not in ("all", "null", ""):
        query = query.filter(Product.location == location)
    count = query.count()
    products = query.offset(skip).limit(limit).all()
    return {"items": products, "count": count}

@router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Get Product Details",
    description="Retrieve detailed information for a specific product by ID as JSON. Requires Authorization header."
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).options(joinedload(Product.country)).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product