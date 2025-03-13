from typing import Iterable, Type, Optional

from sqlalchemy.orm import Session
from sqlalchemy import update, delete, select, DECIMAL
from sqlalchemy.sql.functions import sum
from sqlalchemy.exc import IntegrityError

from .modules import Users, Categories, Carts, Finally_carts, Products, engine

with Session(engine) as session:
    db_session = session


def db_get_user(chat_id: int):
    return db_session.query(Users).filter(Users.telegram == chat_id).first()


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


def db_add_lang(chat_id: int, lang: str):
    """adding user language"""
    query = update(Users).where(Users.telegram == chat_id).values(lang=lang)
    db_session.execute(query)
    db_session.commit()


def db_get_user_lang(chat_id: int):
    return db_session.query(Users.lang).filter(Users.telegram == chat_id).first()


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
    query = update(Carts) \
        .where(Carts.id == cart_id) \
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


def db_get_all_product_inside_finally_cart(chat_id) -> Iterable[Finally_carts]:
    """Get list of products based on telegram id"""
    queue = select(Finally_carts
                   ).join(Carts
                          ).join(Users
                                 ).where(Users.telegram == chat_id)

    return db_session.scalars(queue).fetchall()


def db_get_finally_cart(cart_id: int) -> Finally_carts:
    """get finally cart by id"""
    queue = select(Finally_carts).where(Finally_carts.id == cart_id)
    return db_session.scalar(queue)


def db_update_finally_cart(cart_id: int, new_price: DECIMAL, new_quantity: DECIMAL):
    """update finally cart's price and quantity"""
    try:
        queue = update(Finally_carts
                       ).where(Finally_carts.id == cart_id
                               ).values(final_price=new_price, quantity=new_quantity)

        db_session.execute(queue)
        db_session.commit()

    except IntegrityError as ee:
        db_session.rollback()


def db_delete_product_from_finally_cart(cart_id: int):
    try:
        queue = delete(Finally_carts).where(Finally_carts.id == cart_id)
        db_session.execute(queue)
        db_session.commit()
        return True
    except IntegrityError:
        db_session.rollback()
        return False


def db_get_user_info(chat_id: int) -> Users:
    """return user info"""
    query = select(Users).where(Users.telegram == chat_id)
    return db_session.scalar(query)


def db_clear_finally_cart(cart_id: int) -> None:
    query = delete(Finally_carts).where(Finally_carts.cart_id == cart_id)
    db_session.execute(query)


def db_add_category(category_name):
    """Add a new category to the database"""
    try:
        category = Categories(category_name=category_name)
        db_session.add(category)
        db_session.commit()
        return True
    except IntegrityError:
        return False


def db_add_product(category_id, product_name, description, price, image):
    """Add a new product to the database"""
    try:
        product = Products(
            category_id=category_id,
            product_name=product_name,
            description=description,
            price=price,
            image=image
        )
        db_session.add(product)
        db_session.commit()
        return True
    except IntegrityError:
        return False


def db_get_all_categories():
    """get all categories from database"""
    return db_session.query(Categories).all()


def db_get_category(category_id: int) -> Optional[Type[Categories]]:
    """get category"""
    return db_session.query(Categories).filter(Categories.id == category_id).first()


def db_get_all_products():
    """get all products from database"""
    return db_session.query(Products).all()


def db_get_product_by_id(product_id) -> Optional[Type[Products]]:
    return db_session.query(Products).filter(Products.id == product_id).first()


def db_delete_category(category_id):
    try:
        products = db_session.query(Products).filter(Products.category_id == category_id).all()
        for product in products:
            db_session.delete(product)

        category = db_session.query(Categories).filter(Categories.id == category_id).first()
        if category:
            db_session.delete(category)
            db_session.commit()
            return True

        return False

    except Exception as e:
        print(f"Error deleting category: {e}")
        return False


def db_delete_product(product_id):
    "Delete product by id"
    try:
        product = db_session.query(Products).filter(Products.id == product_id).first()
        if product:
            db_session.delete(product)
            db_session.commit()
            return True
        return False
    except Exception as e:
        print(f"Error whiling deleting product: {e}")
        return False


def db_update_product(product_id, name, description, price, image):
    """ Update product details"""
    try:
        product = db_session.query(Products).filter(Products.id == product_id).first()
        if product:
            product.product_name = name
            product.description = description
            product.price = price
            product.image = image
            db_session.commit()
            return True

        return False
    except IntegrityError:
        return False


def db_update_category(category_id, name):
    try:
        category = db_session.query(Categories).filter(Categories.id == category_id).first()
        if category:
            category.category_name = name
            db_session.commit()
            return True

        return False
    except IntegrityError:
        return False
