import asyncio

from os import getenv
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv

from keyboards.inline_kb import *
from keyboards.reply_kb import *
from database.utils import *
from utils.helper import *


load_dotenv()

TOKEN = getenv('TOKEN')

dp = Dispatcher()
bot = Bot(TOKEN,
          default=DefaultBotProperties(
              parse_mode=ParseMode.HTML,
          )
          )


@dp.message(CommandStart())
async def command_start(message: Message):
    """start bot"""
    await message.answer(f"Hello <b>{message.from_user.full_name} </b>\n"
                         f"Greetings from fast food bot Roxat")

    await user_register(message)


async def user_register(message: Message):
    chat_id = message.chat.id
    user_name = message.from_user.full_name

    if db_register_user(user_name, chat_id):
        await message.answer(text="Authorization completed successfully")
        await show_main_menu(message)
    else:
        await message.answer(text="To connect with you we need your phone number",
                             reply_markup=share_phono_button())


@dp.message(F.contact)
async def update_user_contact(message: Message):
    """Update user contact info"""
    chat_id = message.chat.id
    phone = message.contact.phone_number

    dp_update_user(chat_id, phone)
    if db_create_user_cart(chat_id):
        await message.answer(text="Registration completed successfully")

    await show_main_menu(message)


async def show_main_menu(message: Message):
    """Show main menu buttons"""
    await message.answer(text="Choose your category",
                         reply_markup=generate_main_menu())


@dp.message(F.text == "✅ Make an order")
async def make_order(message: Message):
    """ordering function"""
    chat_id = message.chat.id
    # TODO Get user's cart id
    await bot.send_message(chat_id=chat_id,
                           text="Let's go",
                           reply_markup=back_to_main_menu())

    await message.answer(text="Choose category",
                         reply_markup=generate_category_menu())


@dp.message(F.text == "📝Main menu")
async def return_to_main_menu(message: Message):
    """back to main menu"""
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id - 1)
    await show_main_menu(message)


@dp.callback_query(F.data.regexp(r'category_[1-9]'))
async def show_product_button(call: CallbackQuery):
    """Show all products by chosen category"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    category_id = int(call.data.split('_')[-1])

    await bot.delete_message(chat_id=chat_id,
                             message_id=message_id)

    await bot.send_message(text="Choose product",
                           chat_id=chat_id,
                           reply_markup=show_product_by_category(category_id))


@dp.callback_query(F.data == 'return_to_category')
async def return_to_category_button(call: CallbackQuery):
    """return to select product categories"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_text(chat_id=chat_id,
                                message_id=message_id,
                                text="Choose category",
                                reply_markup=generate_category_menu()
                                )


@dp.callback_query(F.data.contains('product_'))
async def show_product_details(call: CallbackQuery):
    """show selected product details"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    product_id = int(call.data[-1])

    product = db_product_details(product_id)
    await bot.delete_message(chat_id=chat_id,
                             message_id=message_id)

    if user_cart := db_get_user_cart(chat_id):
        db_update_user_cart(price=product.price, cart_id=user_cart.id)
        text = text_for_caption(product_name=product.product_name, price=product.price, description=product.description)

        await bot.send_message(chat_id=chat_id,
                               text="Choose modification",
                               reply_markup=back_arrow_button())

        await bot.send_photo(chat_id=chat_id,
                             photo=FSInputFile(path=product.image),
                             caption=text,
                             reply_markup=generate_constructor_button()
                             )

    else:
        await bot.send_message(chat_id=chat_id,
                               text="Sorry you did not share your phone number",
                               reply_markup=share_phono_button())


@dp.message(F.text == '⬅️Go Back')
async def return_to_category_menu(message: Message):
    """Back to product selection"""
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    await make_order(message)


@dp.callback_query(F.data.regexp(r'action [+-]'))
async def increase_product_quantity(call: CallbackQuery):
    """Increase quantity of product"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    product_name = call.message.caption.split("\n")[0].strip()
    action = call.data.split()[-1]

    product = db_get_product_by_name(product_name)
    user_cart = db_get_user_cart(chat_id)

    if action == '+':
        user_cart.total_products += 1
    elif action == '-':
        if user_cart.total_products < 2:
            await call.answer("Can't be less than one")
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
                                         quantity=user_cart.total_products)
                                     )
    except TelegramBadRequest:
        pass


@dp.callback_query(F.data.regexp(r'action [+-]'))
async def decrease_product_quantity(call: CallbackQuery):
    """Decrease quantity of product"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    await bot.send_message(chat_id=chat_id, text="Product decreased")


@dp.message(F.text == "🛒 Carts")
async def show_carts(message: Message):
    await message.answer(text="Carts selected")


@dp.message(F.text == "🛠️Settings")
async def show_settings(message: Message):
    await message.answer(text="Setting is selected")


@dp.message(F.text == "📄 History")
async def show_history(message: Message):
    await message.answer("History is selected")


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
