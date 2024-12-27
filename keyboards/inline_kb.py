from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup

from database.utils import db_get_all_category, db_get_products_by_category


def generate_category_menu() -> InlineKeyboardMarkup:
    """categories buttons"""
    categories = db_get_all_category()
    builder = InlineKeyboardBuilder()
    # TODO sum price of cart
    builder.button(text=f"Your cart (TODO sum)", callback_data="your cart")
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

