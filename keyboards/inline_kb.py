from typing import Iterable

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup

from database.modules import Products, Finally_carts
from database.utils import db_get_all_category, db_get_products_by_category, db_get_price_sum, db_get_user_cart


def generate_category_menu(chat_id: int) -> InlineKeyboardMarkup:
    """categories buttons"""
    categories = db_get_all_category()
    builder = InlineKeyboardBuilder()
    total_price = db_get_price_sum(chat_id)

    builder.button(text=f"Your cart {total_price if total_price else 0} sums 💰", callback_data="your_cart")
    [builder.button(text=category.category_name,
                    callback_data=f'category_{category.id}') for category in categories]

    builder.adjust(1, 2)
    return builder.as_markup()


def show_product_by_category(category_id: int) -> InlineKeyboardMarkup:
    """Product buttons"""
    products = db_get_products_by_category(category_id)
    builder = InlineKeyboardBuilder()

    [builder.button(text=product.product_name,
                    callback_data=f'product_{product.id}') for product in products]
    builder.adjust(2)

    builder.row(
        InlineKeyboardButton(text='⬅ Back', callback_data='return_to_category')
    )
    return builder.as_markup()


def go_back_to_products(category_id: int) -> InlineKeyboardMarkup:
    """Back button for going back to product list"""
    builder = InlineKeyboardBuilder()
    builder.button(text="back", callback_data=f'category_{category_id}')

    return builder.as_markup()


def generate_constructor_button(quantity=1) -> InlineKeyboardMarkup:
    """buttons for selecting quantity of products"""

    builder = InlineKeyboardBuilder()
    builder.button(text="➖", callback_data="action -")
    builder.button(text=str(quantity), callback_data=str(quantity))
    builder.button(text="➕", callback_data="action +")
    builder.button(text="Add to cart 🛒", callback_data="add_to_cart")

    builder.adjust(3, 1)
    return builder.as_markup()


def generate_buttons_for_finally(product_carts: Iterable[Finally_carts]) -> InlineKeyboardMarkup:
    """buttons for buying products from cart and update quantity of products"""
    builder = InlineKeyboardBuilder()
    print(product_carts.__sizeof__())
    if product_carts.__sizeof__() > 0:
        builder.button(text='Purchase🚀', callback_data='purchase')

        for cart in product_carts:
            builder.button(text='➕', callback_data=f'add_{cart.id}')
            builder.button(text=f'{cart.product_name}', callback_data='product')
            builder.button(text='➖', callback_data=f'minus_{cart.id}')
            builder.button(text='❌', callback_data=f'remove_{cart.id}')

        builder.adjust(1, 4)

    return builder.as_markup()
