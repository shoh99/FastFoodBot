import asyncio

from os import getenv
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto, LabeledPrice
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv

from admin.admin_commands import admin_router
from keyboards.inline_kb import *
from keyboards.reply_kb import *
from database.utils import *
from translation import translations
from utils.helper import *
from filters.admin_filters import is_admin
from translation import LANG

load_dotenv()

TOKEN = getenv('TOKEN')
PAYMENT = getenv('PAYMENT')
MANAGER = getenv('MANAGER')
ADMIN_IDS = [int(id) for id in getenv('ADMIN_IDS', '').split(',')]

dp = Dispatcher()
dp.include_router(admin_router)

bot = Bot(TOKEN,
          default=DefaultBotProperties(
              parse_mode=ParseMode.HTML,
          )
          )



def get_translated_text(key):
    # lang = LANG.get(chat_id, "uz")
    return [translations[lang][key] for lang in translations]


@dp.message(CommandStart())
async def command_start(message: Message):
    """start bot"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    full_name = message.from_user.full_name
    print("fullname" + full_name)

    user_lang = db_get_user_lang(chat_id)[0]

    language = user_lang if user_lang else "uz"
    admin_status = is_admin(user_id)

    print("admin status: " + str(admin_status))
    await message.answer(translations[language]["welcome_message"].format(user_name=full_name))
    if admin_status:
        await message.answer(translations[language]["admin_access_detected"])

    await user_register(message)


async def user_register(message: Message):
    chat_id = message.chat.id
    user = db_get_user(chat_id)
    if user:
        user_lang = db_get_user_lang(chat_id)[0]
        print("User lang: " + str(user_lang))
        if not user_lang:
            await message.answer(translations["uz"]["menu_change_language"], reply_markup=language_select_buttons())
            return

        LANG[chat_id] = user_lang
        await show_main_menu(message)
    else:
        await message.answer(text="To connect with you we need your phone number",
                             reply_markup=share_phono_button())


@dp.message(F.contact)
async def update_user_contact(message: Message):
    """Update user contact info"""
    chat_id = message.chat.id
    phone = message.contact.phone_number
    lang = LANG.get(chat_id, "uz")
    dp_update_user(chat_id, phone)
    if db_create_user_cart(chat_id):
        await message.answer(text=translations[lang]["registration_completed"])

    await show_main_menu(message)


async def show_main_menu(message: Message):
    """Show main menu buttons"""
    chat_id = message.chat.id
    user_lang = LANG.get(chat_id, "uz")
    await message.answer(text=translations[user_lang]["main_menu"],
                         reply_markup=generate_main_menu(user_lang))


@dp.message(F.text.in_(get_translated_text("make_an_order")))
async def make_order(message: Message):
    """ordering function"""
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    # TODO Get user's cart id
    await bot.send_message(chat_id=chat_id,
                           text=translations[lang]["lets_go"],
                           reply_markup=back_to_main_menu(lang))

    await message.answer(text=translations[lang]["choose_category"],
                         reply_markup=generate_category_menu(chat_id, lang))


@dp.message(F.text.in_(get_translated_text("main_menu_button")))
async def return_to_main_menu(message: Message):
    """back to main menu"""
    try:
        await bot.delete_message(chat_id=message.chat.id,
                                 message_id=message.message_id - 1)
        await show_main_menu(message)
    except TelegramBadRequest as e:
        print(e.message)


@dp.callback_query(F.data.regexp(r'category_[1-9]'))
async def show_product_button(call: CallbackQuery):
    """Show all products by chosen category"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    category_id = int(call.data.split('_')[-1])
    lang = LANG.get(chat_id, "uz")
    await bot.delete_message(chat_id=chat_id,
                             message_id=message_id)

    await bot.send_message(text=translations[lang]["choose_product"],
                           chat_id=chat_id,
                           reply_markup=show_product_by_category(category_id, lang))


@dp.callback_query(F.data == 'return_to_category')
async def return_to_category_button(call: CallbackQuery):
    """return to select product categories"""
    chat_id = call.message.chat.id
    lang = LANG.get(chat_id, "uz")
    message_id = call.message.message_id

    await bot.edit_message_text(chat_id=chat_id,
                                message_id=message_id,
                                text=translations[lang]["choose_category"],
                                reply_markup=generate_category_menu(chat_id)
                                )


@dp.callback_query(F.data.startswith('product_'))
async def show_product_details(call: CallbackQuery):
    """show selected product details"""
    chat_id = call.message.chat.id
    lang = LANG.get(chat_id, "uz")
    message_id = call.message.message_id
    product_id = int(call.data[-1])

    product = db_product_details(product_id)
    await bot.delete_message(chat_id=chat_id,
                             message_id=message_id)

    if user_cart := db_get_user_cart(chat_id):
        db_update_user_cart(price=product.price, cart_id=user_cart.id)
        text = text_for_caption(product_name=product.product_name, price=product.price, description=product.description)

        await bot.send_message(chat_id=chat_id,
                               text=translations[lang]["choose_modification"],
                               reply_markup=back_arrow_button())

        await bot.send_photo(chat_id=chat_id,
                             photo=FSInputFile(path=product.image),
                             caption=text,
                             reply_markup=generate_constructor_button(lang)
                             )

    else:
        await bot.send_message(chat_id=chat_id,
                               text=translations[chat_id]["phone_number_required"],
                               reply_markup=share_phono_button())


@dp.message(F.text.in_(get_translated_text("go_back_button")))
async def return_to_category_menu(message: Message):
    """Back to product selection"""
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
        await make_order(message)
    except TelegramBadRequest:
        pass


@dp.callback_query(F.data.regexp(r'action [+-]'))
async def increase_product_quantity(call: CallbackQuery):
    """Increase quantity of product"""
    chat_id = call.message.chat.id
    lang = LANG.get(chat_id, "uz")
    message_id = call.message.message_id
    product_name = call.message.caption.split("\n")[0].strip()
    action = call.data.split()[-1]

    product = db_get_product_by_name(product_name)
    user_cart = db_get_user_cart(chat_id)

    if action == '+':
        user_cart.total_products += 1
    elif action == '-':
        if user_cart.total_products < 2:
            await call.answer(translations[lang]["quantity_minimum"])
        else:
            user_cart.total_products -= 1

    product_price = product.price * user_cart.total_products
    db_update_user_cart(price=product_price,
                        cart_id=user_cart.id,
                        quantity=user_cart.total_products)

    text = text_for_caption(product_name=product.product_name, price=product_price, description=product.description)

    try:
        await bot.edit_message_media(chat_id=chat_id,
                                     message_id=message_id,
                                     media=InputMediaPhoto(
                                         media=FSInputFile(path=product.image),
                                         caption=text
                                     ),
                                     reply_markup=generate_constructor_button(
                                         lang,
                                         quantity=user_cart.total_products)
                                     )
    except TelegramBadRequest:
        pass


@dp.callback_query(F.data == 'add_to_cart')
async def put_products_to_cart(call: CallbackQuery):
    """Put products to cart"""
    try:
        chat_id = call.message.chat.id
        lang = LANG.get(chat_id, "uz")
        message_id = call.message.message_id
        product_name = call.message.caption.split("\n")[0].strip()
        product = db_get_product_by_name(product_name)
        user_cart = db_get_user_cart(chat_id)

        await bot.delete_message(chat_id=chat_id,
                                 message_id=message_id)

        if db_insert_or_update_finally_cart(cart_id=user_cart.id,
                                            product_name=product_name,
                                            total_products=user_cart.total_products,
                                            total_price=user_cart.total_price):

            await bot.send_message(chat_id=chat_id,
                                   text=translations[lang]["added_to_cart"].format(product_name))
        else:
            await bot.send_message(chat_id=chat_id,
                                   text=translations[lang]["updated_in_cart".format(product_name)])

        await return_to_category_menu(call.message)

    except TelegramBadRequest:
        pass


@dp.callback_query(F.data == 'your_cart')
async def show_product_inside_cart(call: CallbackQuery):
    try:
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        lang = LANG.get(chat_id, "uz")
        await bot.delete_message(chat_id=chat_id,
                                 message_id=message_id)

        text, cart_products = count_products_from_cart(chat_id, "Test")
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=generate_buttons_for_finally(lang, cart_products))

    except TelegramBadRequest as e:
        print(e.message)


@dp.callback_query(F.data.regexp(r'^(add_|minus_|remove_)'))
async def update_finally_cart_products(call: CallbackQuery):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    lang = LANG.get(chat_id, "uz")
    cart_id = call.data.split('_')[-1].strip()
    action = call.data.split('_')[0].strip()

    finally_cart = db_get_finally_cart(int(cart_id))
    product = db_get_product_by_name(finally_cart.product_name)
    if action == 'remove':
        if db_delete_product_from_finally_cart(int(cart_id)):
            await call.answer(text=f"Product removed from cart")

    new_price = 0
    new_quantity = 0
    if product:
        if action == 'add':
            new_price = finally_cart.final_price + product.price
            new_quantity = finally_cart.quantity + 1
        elif action == 'minus':
            new_price = finally_cart.final_price - product.price
            new_quantity = finally_cart.quantity - 1
    else:
        await call.answer(text=translations[lang]["product_not_exist"])

    if new_quantity > 0:
        db_update_finally_cart(int(cart_id), new_price, new_quantity)
    else:
        if db_delete_product_from_finally_cart(int(cart_id)):
            product_name = product.product_name if product else "Product"
            await call.answer(text=translations[lang]["removed_from_cart"])

    text, cart_products = count_products_from_cart(chat_id, "Test")
    await bot.edit_message_text(chat_id=chat_id,
                                text=text,
                                message_id=message_id,
                                reply_markup=generate_buttons_for_finally(lang, cart_products)
                                )



@dp.callback_query(F.data == 'purchase')
async def create_order(call: CallbackQuery):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    lang = LANG.get(chat_id, "uz")
    await bot.delete_message(chat_id=chat_id, message_id=message_id)

    content = count_products_for_purchase(chat_id)
    print(content)

    text = content[0]
    total_price = content[1]

    await bot.send_invoice(chat_id=chat_id,
                           title=translations[lang]["your_order"],
                           description=text,
                           payload="bot-defined invoice payload",
                           provider_token=PAYMENT,
                           currency="UZS",
                           prices=[
                               LabeledPrice(label="Total price", amount=int(total_price) * 100),
                               LabeledPrice(label="Delivery", amount=10000)
                           ])
    await bot.send_message(chat_id=chat_id, text=translations[lang]["purchase_completed"])
    await sending_report_to_manager(chat_id, text)
    user_cart = db_get_user_cart(chat_id)
    db_clear_finally_cart(user_cart.id)


async def sending_report_to_manager(chat_id: int, text: str):
    """Sending message to group chat"""
    user = db_get_user_info(chat_id)
    text += f"\n\n<b>Customer name: {user.name}\nContact: {user.phone}</b>\n\n"

    await bot.send_message(chat_id=MANAGER, text=text)


@dp.message(F.text.in_(get_translated_text("carts_main_menu")))
async def show_carts(message: Message):
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    await message.answer(text=translations[lang]["carts_selected"])


@dp.message(F.text.in_(get_translated_text("settings_main_menu")))
async def show_settings(message: Message):
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    user_id = message.from_user.id
    admin_status = is_admin(user_id)
    await message.answer(text=translations[lang]["setting_selected"],
                         reply_markup=setting_commands(admin_status, lang))


@dp.message(F.text.in_(get_translated_text("history_main_menu")))
async def show_history(message: Message):
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    await message.answer(translations[lang]["history_selected"])


@dp.message(F.text.in_(get_translated_text("change_language_setting")))
async def change_language_settings(message: Message):
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    await message.answer(translations[lang]["menu_change_language"], reply_markup=language_select_buttons())


@dp.message(F.text == "UZ 🇺🇿")
async def change_to_uzb(message: Message):
    chat_id = message.chat.id
    LANG[chat_id] = "uz"
    db_add_lang(chat_id, "uz")
    await message.answer("O'zbek tili sozlandi!")
    await show_main_menu(message)


@dp.message(F.text == "RU 🇷🇺")
async def change_to_ru(message: Message):
    chat_id = message.chat.id
    LANG[chat_id] = "ru"
    db_add_lang(chat_id, "ru")
    await message.answer("Русский язык установлен!")
    await show_main_menu(message)


@dp.message(F.text == "ENG 🏴󠁧󠁢󠁥󠁮󠁧󠁿")
async def change_to_eng(message: Message):
    chat_id = message.chat.id
    LANG[chat_id] = "en"
    db_add_lang(chat_id, "en")
    await message.answer("English language installed!")
    await show_main_menu(message)


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
