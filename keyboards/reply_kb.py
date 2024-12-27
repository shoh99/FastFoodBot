from aiogram.utils.keyboard import ReplyKeyboardMarkup, ReplyKeyboardBuilder


def share_phono_button() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Share your phone number ☎️", request_contact=True)
    return builder.as_markup()


def generate_main_menu() -> ReplyKeyboardMarkup:
    """main menu button"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="✅ Make an order")
    builder.button(text="📄 History")
    builder.button(text="🛒 Carts")
    builder.button(text="🛠️Settings")

    builder.adjust(1, 3)
    return builder.as_markup()


def back_to_main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Main menu")

    return builder.as_markup()

