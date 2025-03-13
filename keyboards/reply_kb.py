from aiogram.utils.keyboard import ReplyKeyboardMarkup, ReplyKeyboardBuilder
from translation import translations

def share_phono_button() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Share your phone number ☎️", request_contact=True)
    return builder.as_markup(resize_keyboard=True)


def generate_main_menu(user_lang) -> ReplyKeyboardMarkup:
    """main menu button"""
    builder = ReplyKeyboardBuilder()
    builder.button(text=translations[user_lang]["make_order_main_menu"])
    builder.button(text=translations[user_lang]["history_main_menu"])
    builder.button(text=translations[user_lang]["carts_main_menu"])
    builder.button(text=translations[user_lang]["settings_main_menu"])

    builder.adjust(1, 3)
    return builder.as_markup(resize_keyboard=True)


def back_to_main_menu(lang) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=translations[lang]["main_menu_button"])

    return builder.as_markup(resize_keyboard=True)


def back_arrow_button(lang) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=translations[lang]["go_back_button"])
    return builder.as_markup(resize_keyboard=True)


def setting_commands(is_admin, lang) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    if is_admin:
        builder.button(text="🔐Admin")

    builder.button(text=translations[lang]["change_language_setting"])
    builder.button(text=translations[lang]["main_menu_button_text"])
    return builder.as_markup(resize_keyboard=True)


def language_select_buttons() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="UZ 🇺🇿")
    builder.button(text="RU 🇷🇺")
    builder.button(text="ENG 🏴󠁧󠁢󠁥󠁮󠁧󠁿")

    return builder.as_markup(resize_keyboard=True)
