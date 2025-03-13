from typing import Iterable

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup

from database.modules import Products, Finally_carts
from database.utils import db_get_all_category, db_get_products_by_category, db_get_price_sum, db_get_user_cart
from translation import translations


def generate_category_menu(chat_id: int, lang: str) -> InlineKeyboardMarkup:
    """categories buttons"""
    categories = db_get_all_category()
    builder = InlineKeyboardBuilder()
    total_price = db_get_price_sum(chat_id)

    # Use translated text for "Your cart" button
    cart_text_key = "your_cart_button"
    cart_text = translations[lang][cart_text_key].format(total_price=total_price if total_price else 0)
    builder.button(text=cart_text, callback_data="your_cart")

    [builder.button(text=category.category_name,
                    callback_data=f'category_{category.id}') for category in categories]

    builder.adjust(1, 2)
    return builder.as_markup()


def show_product_by_category(category_id: int, user_language: str) -> InlineKeyboardMarkup:
    """Product buttons"""
    products = db_get_products_by_category(category_id)
    builder = InlineKeyboardBuilder()

    [builder.button(text=product.product_name,
                    callback_data=f'product_{product.id}') for product in products]
    builder.adjust(2)

    # Use translated text for "Back" button
    back_text_key = "back_button"
    back_text = translations[user_language][back_text_key]
    builder.row(
        InlineKeyboardButton(text=back_text, callback_data='return_to_category')
    )
    return builder.as_markup()


def go_back_to_products(category_id: int, user_language) -> InlineKeyboardMarkup:
    """Back button for going back to product list"""
    builder = InlineKeyboardBuilder()
    # Use translated text for "back" button
    back_to_prod_text_key = "back_to_products_button"
    back_to_prod_text = translations[user_language][back_to_prod_text_key]
    builder.button(text=back_to_prod_text, callback_data=f'category_{category_id}')

    return builder.as_markup()


def generate_constructor_button(user_language, quantity=1) -> InlineKeyboardMarkup:
    """buttons for selecting quantity of products"""

    builder = InlineKeyboardBuilder()
    # Use translated text for quantity decrease button
    quantity_decrease_text_key = "quantity_decrease"
    quantity_decrease_text = translations[user_language][quantity_decrease_text_key]
    builder.button(text=quantity_decrease_text, callback_data="action -")
    builder.button(text=str(quantity), callback_data=str(quantity))
    # Use translated text for quantity increase button
    quantity_increase_text_key = "quantity_increase"
    quantity_increase_text = translations[user_language][quantity_increase_text_key]
    builder.button(text=quantity_increase_text, callback_data="action +")
    # Use translated text for "Add to cart" button
    add_to_cart_text_key = "add_to_cart_button"
    add_to_cart_text = translations[user_language][add_to_cart_text_key]
    builder.button(text=add_to_cart_text, callback_data="add_to_cart")

    builder.adjust(3, 1)
    return builder.as_markup()


def generate_buttons_for_finally(user_language, product_carts: Iterable[Finally_carts]) -> InlineKeyboardMarkup:
    """buttons for buying products from cart and update quantity of products"""
    builder = InlineKeyboardBuilder()
    print(product_carts.__sizeof__())
    if product_carts.__sizeof__() > 0:
        # Use translated text for "Purchase" button
        purchase_text_key = "purchase_button"
        purchase_text = translations[user_language][purchase_text_key]
        builder.button(text=purchase_text, callback_data='purchase')

        for cart in product_carts:
            # Use translated text for quantity increase button
            quantity_increase_text_key = "quantity_increase"
            quantity_increase_text = translations[user_language][quantity_increase_text_key]
            builder.button(text=quantity_increase_text, callback_data=f'add_{cart.id}')
            builder.button(text=f'{cart.product_name}', callback_data='product')
            # Use translated text for quantity decrease button
            quantity_decrease_text_key = "quantity_decrease"
            quantity_decrease_text = translations[user_language][quantity_decrease_text_key]
            builder.button(text=quantity_decrease_text, callback_data=f'minus_{cart.id}')
            # Use translated text for "Remove" button
            remove_item_text_key = "remove_item_button"
            remove_item_text = translations[user_language][remove_item_text_key]
            builder.button(text=remove_item_text, callback_data=f'remove_{cart.id}')

        builder.adjust(1, 4)

    return builder.as_markup()


def generate_categories_for_admin(categories):
    """Generate keyboard with categories for admin"""
    keyboard = []
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{category.category_name}",
                callback_data=f"admin_category_{category.id}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def generate_categories_for_admin_edit(categories):
    """Generate keyboard with categories for admin"""
    keyboard = []
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{category.category_name}",
                callback_data=f"admin_category_edit_{category.id}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def generate_products_for_admin(products):
    """Generate keyboard with products for admin"""
    keyboards = []
    for product in products:
        keyboards.append([
            InlineKeyboardButton(
                text=f"{product.product_name}",
                callback_data=f"admin_prod_{product.id}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboards)


def generate_edit_product_keyboard(product_id, user_language):
    """Generate keyboard for product editing"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=translations[user_language]["edit_button"],
                callback_data=f"edit_product_{product_id}"
            ),
            InlineKeyboardButton(
                text=translations[user_language]["delete_button"],
                callback_data=f"delete_product_{product_id}"
            ),
            InlineKeyboardButton(
                text="🔙",
                callback_data="return_to_products"
            ),
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def generate_edit_category_keyboard(user_language, id):
    """Generate keyboard for product editing"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=translations[user_language]["edit_button"],
                callback_data=f"edit_category_{id}"
            ),
            InlineKeyboardButton(
                text=translations[user_language]["delete_button"],
                callback_data=f"delete_category_{id}"
            ),
            InlineKeyboardButton(
                text="🔙",
                callback_data="return_to_categories"
            ),
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def generate_confirm_delete_keyboard(item_type, item_id, lang):
    """Generate keyboard for confirming deletion"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=translations[lang]["confirm_delete_yes"],
                callback_data=f"confirm_delete_{item_type}_{item_id}"
            ),
            InlineKeyboardButton(
                text=translations[lang]["confirm_delete_no"],
                callback_data=f"cancel_delete_{item_type}"
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
