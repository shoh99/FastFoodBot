from os import getenv

from sqlalchemy.orm import DeclarativeBase, Mapped, relationship, Session
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, Integer, BigInteger, DECIMAL, ForeignKey, UniqueConstraint
from sqlalchemy import create_engine
from dotenv import load_dotenv



class Base(DeclarativeBase):
    pass


class Users(Base):
    """Users Table"""

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    telegram: Mapped[int] = mapped_column(BigInteger, unique=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=True)
    lang: Mapped[str] = mapped_column(String(30), nullable=True)
    carts: Mapped[int] = relationship('Carts', back_populates='user_cart')

    def __str__(self):
        return self.name


class Carts(Base):
    """Temporary cart for customers, used till cashier"""

    __tablename__ = "carts"
    id: Mapped[int] = mapped_column(primary_key=True)
    total_price: Mapped[int] = mapped_column(DECIMAL(12, 2), default=0)
    total_products: Mapped[int] = mapped_column(default=0)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), unique=True)

    user_cart: Mapped[Users] = relationship(back_populates='carts')
    finally_id: Mapped[int] = relationship("Finally_carts", back_populates='user_cart')

    def __str__(self):
        return str(self.id)


class Finally_carts(Base):
    """Final cart which used for purchasing"""
    __tablename__ = "finally_carts"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(String(50))
    final_price: Mapped[DECIMAL] = mapped_column(DECIMAL(12, 2))
    quantity: Mapped[int]

    cart_id: Mapped[int] = mapped_column(ForeignKey('carts.id'))
    user_cart: Mapped[Carts] = relationship(back_populates='finally_id')

    __table_args__ = (UniqueConstraint('cart_id', 'product_name'),)

    def __str__(self):
        return str(self.id)


class Categories(Base):
    """Product categories"""
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    category_name: Mapped[str] = mapped_column(String(20), unique=True)

    products: Mapped[list['Products']] = relationship('Products', back_populates='product_category')

    def __str__(self):
        return self.category_name


class Products(Base):
    """Products table"""
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(String(30), unique=True)
    description: Mapped[str]
    image: Mapped[str]
    price: Mapped[DECIMAL] = mapped_column(DECIMAL(12, 2))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))

    product_category: Mapped[Categories] = relationship('Categories', back_populates='products')

    def __str__(self):
        return self.product_name

