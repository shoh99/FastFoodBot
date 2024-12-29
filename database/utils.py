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


def db_get_user_cart(chat_id: int) -> Carts:
    query = select(Carts).join(Users).where(Users.telegram == chat_id)
    return db_session.scalar(query)


def db_update_user_cart(price: DECIMAL, cart_id: int, quantity=1):
    query = update(Carts)\
        .where(Carts.id == cart_id)\
        .values(total_price=price, total_products=quantity)

    db_session.execute(query)
    db_session.commit()


def db_get_product_by_name(product_name: str) -> Products:
    query = select(Products).where(Products.product_name == product_name)
    return db_session.scalar(query)


def db_insert_or_update_finally_cart(cart_id: int, product_name: str, total_products: int, total_price: int) -> bool:
    """Insert or update finally cart"""
    try:
        query = Finally_carts(cart_id=cart_id,
                              product_name=product_name,
                              quantity=total_products,
                              final_price=total_price)

        db_session.add(query)
        db_session.commit()
        return True
    except IntegrityError:
        db_session.rollback()
        query = update(Finally_carts
                       ).where(Finally_carts.product_name == product_name
                               ).where(Finally_carts.cart_id == cart_id
                                       ).values(quantity=total_products, final_price=total_price)

        update(Finally_carts).where()
        db_session.execute(query)
        db_session.commit()
        return False


def db_save_finally_cart(product_name: str, quantity: int, final_price: DECIMAL, cart: Carts):
    try:
        query = Finally_carts(product_name=product_name,
                              final_price=final_price,
                              quantity=quantity,
                              user_cart=cart)

        db_session.add(query)
        db_session.commit()
    except IntegrityError:
        db_session.rollback()
    except AttributeError:
        db_session.rollback()


def db_get_price_sum(chat_id: int):
    queue = select(sum(Finally_carts.final_price)
           ).join(Carts
                  ).join(Users
                         ).where(Users.telegram == chat_id)

    return db_session.execute(queue).fetchone()[0]

