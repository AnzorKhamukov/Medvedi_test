from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from celery import Celery

Base = declarative_base()


class Product(Base):
    __tablename__ = 'products'

    nm_id = Column(Integer, primary_key=True)
    current_price = Column(Float)
    sum_quantity = Column(Integer)


class ProductSize(Base):
    __tablename__ = 'product_sizes'

    id = Column(Integer, primary_key=True)
    nm_id = Column(Integer)
    size = Column(String)
    quantity_by_wh = Column(Integer)


app = Celery('tasks', broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0'
             )

app.conf.beat_schedule = {
    'update-product-data': {
        'task': 'tasks.update_product_data',
        'schedule': 300.0,
    },
}

#конфигурация БД
engine = create_engine(
    'postgresql+psycopg2://postgres:password@localhost:5432/database_name'
    )
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

app = FastAPI()


class ProductRequest(BaseModel):
    nm_id: int


@app.get('/product')
async def get_product(request: Request, prod_request: ProductRequest):
    session = Session()
    product = session.query(
        Product).filter(Product.nm_id == prod_request.nm_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product_sizes = session.query(
        ProductSize).filter(ProductSize.nm_id == prod_request.nm_id).all()

    response = {
        "nm_id": product.nm_id,
        "current_price": product.current_price,
        "sum_quantity": product.sum_quantity,
        "quantity_by_sizes": [
            {
                "size": size.size,
                "quantity_by_wh": [
                    {
                        "wh": size.quantity_by_wh,
                        "quantity": size.quantity
                    }
                ]
            } for size in product_sizes
        ]
    }

    return response


@app.post('/product')
async def create_product(request: Request, product_create: ProductRequest):
    session = Session()
    if not session.query(Product).filter(Product.nm_id == product_create.nm_id).first():
        product = Product(nm_id=product_create.nm_id)
        session.add(product)
        session.commit()

    return {"status": "ok"}


@app.put('/product')
async def update_product(request: Request, product_update: ProductRequest):
    session = Session()
    product = session.query(Product).filter(
        Product.nm_id == product_update.nm_id).first()
    if product:
        product.current_price = product_update.current_price
        product.sum_quantity = product_update.current_quantity
        session.commit()

    return {"status": "ok"}


@app.delete('/product')
async def delete_product(request: Request, product_delete: ProductRequest):
    session = Session()
    product = session.query(Product).filter(
        Product.nm_id == product_delete.nm_id).first()
    if product:
        session.delete(product)
        session.commit()

    return {"status": "ok"}
