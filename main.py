import asyncio

from os import getenv
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto, LabeledPrice
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv

from keyboards.inline_kb import *
from keyboards.reply_kb import *
from database.utils import *
from utils.helper import *

load_dotenv()

TOKEN = getenv('TOKEN')
PAYMENT = getenv('PAYMENT')
MANAGER = getenv('MANAGER')

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
                         reply_markup=generate_category_menu(chat_id))


@dp.message(F.text == "📝Main menu")
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
                                reply_markup=generate_category_menu(chat_id)
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
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
        await make_order(message)
    except TelegramBadRequest:
        pass


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


@dp.callback_query(F.data == 'add_to_cart')
async def put_products_to_cart(call: CallbackQuery):
    """Put products to cart"""
    try:
        chat_id = call.message.chat.id
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
                                   text=f"{product_name} added ➕to your cart 🛒")
        else:
            await bot.send_message(chat_id=chat_id,
                                   text=f"{product_name} updated ✏️ in your cart 🛒")

        await return_to_category_menu(call.message)

    except TelegramBadRequest:
        pass


@dp.callback_query(F.data == 'your_cart')
async def show_product_inside_cart(call: CallbackQuery):
    try:
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        await bot.delete_message(chat_id=chat_id,
                                 message_id=message_id)

        text, cart_products = count_products_from_cart(chat_id, "Test")
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=generate_buttons_for_finally(cart_products))

    except TelegramBadRequest as e:
        print(e.message)


@dp.callback_query(F.data.regexp(r'^(add_|minus_|remove_)'))
async def update_finally_cart_products(call: CallbackQuery):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    cart_id = call.data.split('_')[-1].strip()
    action = call.data.split('_')[0].strip()

    finally_cart = db_get_finally_cart(int(cart_id))
    product = db_get_product_by_name(finally_cart.product_name)

    new_price = 0
    new_quantity = 0
    if action == 'remove':
        if db_delete_product_from_finally_cart(int(cart_id)):
            await call.answer(text=f"{product.product_name} removed from cart")
    else:
        if action == 'add':
            new_price = finally_cart.final_price + product.price
            new_quantity = finally_cart.quantity + 1
        elif action == 'minus':
            new_price = finally_cart.final_price - product.price
            new_quantity = finally_cart.quantity - 1

        if new_quantity > 0:
            db_update_finally_cart(int(cart_id), new_price, new_quantity)
        else:
            if db_delete_product_from_finally_cart(int(cart_id)):
                await call.answer(text=f"{product.product_name} removed from cart")

    text, cart_products = count_products_from_cart(chat_id, "Test")
    await bot.edit_message_text(chat_id=chat_id,
                                text=text,
                                message_id=message_id,
                                reply_markup=generate_buttons_for_finally(cart_products)
                                )


@dp.callback_query(F.data == 'purchase')
async def create_order(call: CallbackQuery):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.delete_message(chat_id=chat_id, message_id=message_id)

    content = count_products_for_purchase(chat_id)
    print(content)

    text = content[0]
    total_price = content[1]

    await bot.send_invoice(chat_id=chat_id,
                           title="Your order",
                           description=text,
                           payload="bot-defined invoice payload",
                           provider_token=PAYMENT,
                           currency="UZS",
                           prices=[
                               LabeledPrice(label="Total price", amount=int(total_price) * 100),
                               LabeledPrice(label="Delivery", amount=10000)
                           ])
    await bot.send_message(chat_id=chat_id, text="Your Purchase Completed")
    await sending_report_to_manager(chat_id, text)
    user_cart = db_get_user_cart(chat_id)
    db_clear_finally_cart(user_cart.id)


async def sending_report_to_manager(chat_id: int, text: str):
    """Sending message to group chat"""
    user = db_get_user_info(chat_id)
    text += f"\n\n<b>Customer name: {user.name}\nContact: {user.phone}</b>\n\n"

    await bot.send_message(chat_id=MANAGER, text=text)


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
