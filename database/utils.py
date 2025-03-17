import logging
from contextlib import contextmanager
from functools import wraps
from os import getenv
from sqlite3 import OperationalError
from typing import Iterable, Type, Optional

from dotenv import load_dotenv
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import update, delete, select, DECIMAL, create_engine, Engine, QueuePool
from sqlalchemy.sql.functions import sum
from sqlalchemy.exc import IntegrityError, DisconnectionError

from .modules import Users, Categories, Carts, Finally_carts, Products

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_USER = getenv('DB_USER')
DB_PASSWORD = getenv('DB_PASSWORD')
DB_ADDRESS = getenv('DB_HOST')
DB_NAME = getenv('DB_NAME')


def get_db_engine() -> Engine:
    """Create and return a SQLAlchemy engine with connection string"""
    connection_string = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_ADDRESS}/{DB_NAME}'
    engine = create_engine(
        connection_string,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=300,
        pool_pre_ping=True,
        echo=True
    )
    return engine


# Initialize engine and session factory
engine = get_db_engine()
SessionFactory = sessionmaker(bind=engine)


@contextmanager
def get_db_session():
    """context manager for database sessions"""
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Database error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def db_session_handler(func):
    """decorator to handle database sessions and retries"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                with get_db_session() as session:
                    result = func(session=session, *args, **kwargs)

                    if result is not None:
                        if hasattr(result, 'all'):
                            result = result.all()

                        if isinstance(result, list) and result and hasattr(result[0], "__dict__") and hasattr(result[0],
                                                                                                              "__tablename__"):
                            result = [_convert_sa_object_to_dict(obj) for obj in result]
                        elif hasattr(result, "__dict__") and hasattr(result, "__tablename__"):
                            result = _convert_sa_object_to_dict(result)

                    return result
            except (OperationalError, DisconnectionError) as e:
                retry_count += 1
                logger.warning(f"Database connection error: {e}. Retry {retry_count}/{max_retries}")
                if retry_count >= max_retries:
                    logger.error(f"Failed after {max_retries} retries: {e}")
                    raise

            except Exception as e:
                logger.error(f"Unhandled database error: {e}")
                raise

    return wrapper


def _convert_sa_object_to_dict(obj):
    if obj is None:
        return None

    data = {}
    for key, value in obj.__dict__.items():
        if not key.startswith("_"):
            if hasattr(value, "__dict__") and hasattr(value, "__tablename__"):
                data[key] = _convert_sa_object_to_dict(value)
            else:
                data[key] = value
    return data


@db_session_handler
def db_get_user(chat_id: int, session: Session = None):
    return session.query(Users).filter(Users.telegram == chat_id).first()


@db_session_handler
def db_register_user(user_name: str, chat_id: int, session: Session = None) -> bool:
    try:
        query = Users(name=user_name, telegram=chat_id)
        session.add(query)
        return False
    except IntegrityError:
        return True


@db_session_handler
def dp_update_user(chat_id: int, phone: str, session: Session = None):
    """adding user contact number"""
    query = update(Users).where(Users.telegram == chat_id).values(phone=phone)
    session.execute(query)


@db_session_handler
def db_add_lang(chat_id: int, lang: str, session: Session = None):
    """adding user language"""
    query = update(Users).where(Users.telegram == chat_id).values(lang=lang)
    session.execute(query)


@db_session_handler
def db_get_user_lang(chat_id: int, session: Session = None):
    return session.query(Users.lang).filter(Users.telegram == chat_id).first()


@db_session_handler
def db_create_user_cart(chat_id: int, session: Session = None):
    """create temporary cart for user"""
    try:
        subquery = session.scalar(select(Users).where(Users.telegram == chat_id))
        query = Carts(user_id=subquery.id)

        session.add(query)
        return True
    except IntegrityError:
        """If cart already exists"""
        return False
    except AttributeError:
        """If anonim user send contact number"""
        return False


@db_session_handler
def db_get_all_category(session: Session = None) -> Iterable:
    query = select(Categories)
    return session.scalars(query)


@db_session_handler
def db_get_products_by_category(category_id: int, session: Session = None) -> Iterable:
    return session.scalars(select(Products).where(Products.category_id == category_id))



@db_session_handler
def db_product_details(product_id: int, session: Session = None) -> Products:
    query = select(Products).where(Products.id == product_id)
    return session.scalar(query)


@db_session_handler
def db_get_user_cart(chat_id: int, session: Session = None) -> Carts:
    query = select(Carts).join(Users).where(Users.telegram == chat_id)
    return session.scalar(query)


@db_session_handler
def db_update_user_cart(price: DECIMAL, cart_id: int, quantity=1, session: Session = None):
    query = update(Carts) \
        .where(Carts.id == cart_id) \
        .values(total_price=price, total_products=quantity)

    session.execute(query)


@db_session_handler
def db_get_product_by_name(product_name: str, session: Session = None) -> Products:
    query = select(Products).where(Products.product_name == product_name)
    return session.scalar(query)


@db_session_handler
def db_insert_or_update_finally_cart(cart_id: int, product_name: str, total_products: int, total_price: int,
                                     session: Session = None) -> bool:
    """Insert or update finally cart"""
    try:
        query = Finally_carts(cart_id=cart_id,
                              product_name=product_name,
                              quantity=total_products,
                              final_price=total_price)

        session.add(query)
        return True
    except IntegrityError:
        query = update(Finally_carts
                       ).where(Finally_carts.product_name == product_name
                               ).where(Finally_carts.cart_id == cart_id
                                       ).values(quantity=total_products, final_price=total_price)

        update(Finally_carts).where()
        session.execute(query)
        return False


@db_session_handler
def db_save_finally_cart(product_name: str, quantity: int, final_price: DECIMAL, cart: Carts, session: Session = None):
    query = Finally_carts(product_name=product_name,
                          final_price=final_price,
                          quantity=quantity,
                          user_cart=cart)

    session.add(query)
    session.commit()


@db_session_handler
def db_get_price_sum(chat_id: int, session: Session = None):
    queue = select(sum(Finally_carts.final_price)
                   ).join(Carts
                          ).join(Users
                                 ).where(Users.telegram == chat_id)

    return session.execute(queue).fetchone()[0]


@db_session_handler
def db_get_all_product_inside_finally_cart(chat_id, session: Session = None) -> Iterable[Finally_carts]:
    """Get list of products based on telegram id"""
    queue = select(Finally_carts
                   ).join(Carts
                          ).join(Users
                                 ).where(Users.telegram == chat_id)

    return session.scalars(queue).fetchall()


@db_session_handler
def db_get_finally_cart(cart_id: int, session: Session = None) -> Finally_carts:
    """get finally cart by id"""
    queue = select(Finally_carts).where(Finally_carts.id == cart_id)
    return session.scalar(queue)


@db_session_handler
def db_update_finally_cart(cart_id: int, new_price: DECIMAL, new_quantity: DECIMAL, session: Session = None):
    """update finally cart's price and quantity"""
    queue = update(Finally_carts
                   ).where(Finally_carts.id == cart_id
                           ).values(final_price=new_price, quantity=new_quantity)

    session.execute(queue)


@db_session_handler
def db_delete_product_from_finally_cart(cart_id: int, session: Session = None):
    try:
        queue = delete(Finally_carts).where(Finally_carts.id == cart_id)
        session.execute(queue)
        return True
    except IntegrityError:
        return False


@db_session_handler
def db_get_user_info(chat_id: int, session: Session = None) -> Users:
    """return user info"""
    query = select(Users).where(Users.telegram == chat_id)
    return session.scalar(query)


@db_session_handler
def db_clear_finally_cart(cart_id: int, session: Session = None) -> None:
    query = delete(Finally_carts).where(Finally_carts.cart_id == cart_id)
    session.execute(query)


@db_session_handler
def db_add_category(category_name, session: Session = None):
    """Add a new category to the database"""
    try:
        category = Categories(category_name=category_name)
        session.add(category)
        return True
    except IntegrityError:
        return False


@db_session_handler
def db_add_product(category_id, product_name, description, price, image, session: Session = None):
    """Add a new product to the database"""
    try:
        product = Products(
            category_id=category_id,
            product_name=product_name,
            description=description,
            price=price,
            image=image
        )
        session.add(product)
        session.commit()
        return True
    except IntegrityError:
        return False


@db_session_handler
def db_get_all_categories(session: Session = None):
    """get all categories from database"""
    return session.query(Categories).all()


@db_session_handler
def db_get_category(category_id: int, session: Session = None) -> Optional[Type[Categories]]:
    """get category"""
    return session.query(Categories).filter(Categories.id == category_id).first()


@db_session_handler
def db_get_all_products(session: Session = None):
    """get all products from database"""
    return session.query(Products).all()


@db_session_handler
def db_get_product_by_id(product_id, session: Session = None) -> Optional[Type[Products]]:
    return session.query(Products).filter(Products.id == product_id).first()


@db_session_handler
def db_delete_category(category_id, session: Session = None):
    try:
        products = session.query(Products).filter(Products.category_id == category_id).all()
        for product in products:
            session.delete(product)

        category = session.query(Categories).filter(Categories.id == category_id).first()
        if category:
            session.delete(category)
            return True

        return False

    except Exception as e:
        logger.error(f"Error deleting category: {e}")
        return False


@db_session_handler
def db_delete_product(product_id, session: Session = None):
    "Delete product by id"
    try:
        product = session.query(Products).filter(Products.id == product_id).first()
        if product:
            session.delete(product)
            return True
        return False
    except Exception as e:
        logger.error(f"Error whiling deleting product: {e}")
        return False


@db_session_handler
def db_update_product(product_id, name, description, price, image, session: Session = None):
    """ Update product details"""
    try:
        product = session.query(Products).filter(Products.id == product_id).first()
        if product:
            product.product_name = name
            product.description = description
            product.price = price
            product.image = image
            return True

        return False
    except IntegrityError:
        return False


@db_session_handler
def db_update_category(category_id, name, session: Session = None):
    try:
        category = session.query(Categories).filter(Categories.id == category_id).first()
        if category:
            category.category_name = name
            return True

        return False
    except IntegrityError:
        return False
