from typing import Iterable

from sqlalchemy.orm import Session
from sqlalchemy import update, delete, select, DECIMAL
from sqlalchemy.sql.functions import sum
from sqlalchemy.exc import IntegrityError

from .modules import Users, Categories, Carts, Finally_carts, Products, engine

with Session(engine) as session:
    db_session = session


def db_register_user(user_name: str, chat_id: int) -> bool:
    try:
        query = Users(name=user_name, telegram=chat_id)
        db_session.add(query)
        db_session.commit()

        return False
    except IntegrityError:
        db_session.rollback()
        return True


def dp_update_user(chat_id: int, phone: str):
    """adding user contact number"""
    query = update(Users).where(Users.telegram == chat_id).values(phone=phone)
    db_session.execute(query)
    db_session.commit()


def db_create_user_cart(chat_id: int):
    """create temporary cart for user"""
    try:
        subquery = db_session.scalar(select(Users).where(Users.telegram == chat_id))
        query = Carts(user_id=subquery.id)

        db_session.add(query)
        db_session.commit()
        return True
    except IntegrityError:
        """If cart already exists"""
        db_session.rollback()
    except AttributeError:
        """If anonim user send contact number"""
        db_session.rollback()


def db_get_all_category() -> Iterable:
    query = select(Categories)
    return db_session.scalars(query)


def db_get_products_by_category(category_id: int) -> Iterable:
    return db_session.scalars(select(Products).where(Products.category_id == category_id))


def db_product_details(product_id: int) -> Products:
    query = select(Products).where(Products.id == product_id)
    return db_session.scalar(query)


def db_get_user_cart(chat_id: int) -> int:
    query = select(Carts.id).join(Users).where(Users.telegram == chat_id)
    return db_session.scalar(query)


def db_update_user_cart(price: DECIMAL, cart_id: int, quantity=1):
    query = update(Carts)\
        .where(Carts.id == cart_id)\
        .values(total_price=price, total_products=quantity)

    db_session.execute(query)
    db_session.commit()