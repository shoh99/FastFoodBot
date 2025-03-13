import os

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.reply_kb import generate_main_menu, setting_commands
from translation import LANG
from translation import translations
from filters.admin_filters import IsAdmin
from aiogram import Bot
from database.utils import (
    db_add_category,
    db_add_product,
    db_get_all_products,
    db_get_all_categories,
    db_delete_category,
    db_update_product,
    db_get_product_by_id, db_delete_product, db_get_category, db_update_category
)

from keyboards.inline_kb import (
    generate_categories_for_admin,
    generate_products_for_admin,
    generate_edit_product_keyboard,
    generate_confirm_delete_keyboard, generate_categories_for_admin_edit, generate_edit_category_keyboard
)

admin_router = Router()


class CategoryForm(StatesGroup):
    name = State()


class EditCategoryForm(StatesGroup):
    category_id = State()
    name = State()


class ProductForm(StatesGroup):
    category_id = State()
    name = State()
    description = State()
    price = State()
    image = State()


class EditProductForm(StatesGroup):
    product_id = State()
    name = State()
    description = State()
    price = State()
    image = State()


class DeleteCategoryForm(StatesGroup):
    category_id = State()


class DeleteProductForm(StatesGroup):
    product_id = State()


@admin_router.message(IsAdmin(), Command("admin"))
async def show_admin_panel(message: Message):
    """Show admin panel commands"""
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    try:
        await message.answer(
           translations[lang]["admin_panel_commands"], reply_markup=setting_commands(True, lang)
        )
    except Exception as e:
        print(f"Exception during show_admin_panel: {str(e)}")


@admin_router.message(F.text == "🔐Admin")
async def show_admin_panel_from_text(message: Message, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    await show_admin_panel(message)


"""
Admin categories management
"""


@admin_router.message(IsAdmin(), Command("addcategory"))
async def add_category_command(message: Message, state: FSMContext):
    """Start category addition process"""
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    await state.set_state(CategoryForm.name)
    await message.answer(translations[lang]["add_category_enter_name"])


@admin_router.message(IsAdmin(), CategoryForm.name)
async def process_category_name(message: Message, state: FSMContext):
    category_name = message.text.strip()
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    success = db_add_category(category_name)
    if success:
        await message.answer(translations[lang]["category_added_success"].format(category_name=category_name))
    else:
        await message.answer(translations[lang]["category_added_fail"])


    await state.clear()


@admin_router.message(IsAdmin(), Command("categories"))
async def list_categories(message: Message):
    """List all categories with management options"""
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    categories = db_get_all_categories()
    if not categories:
        await message.answer(translations[lang]["no_categories_found"])
        return

    text = translations[lang]["categories_list_title"]
    text += translations[lang]["categories_list_instruction"]

    await message.answer(
        text,
        reply_markup=generate_categories_for_admin_edit(categories)
    )


@admin_router.callback_query(F.data.startswith("admin_category_edit_"))
async def manage_selected_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[-1])
    category = db_get_category(category_id)
    chat_id = callback.message.chat.id
    lang = LANG.get(chat_id, "uz")
    if not category:
        await callback.message.answer(translations[lang]["category_not_found"])

    text = translations[lang]["category_name_label"].format(category_name=category.category_name)
    await callback.message.edit_text(text, reply_markup=generate_edit_category_keyboard(lang, category_id))


@admin_router.callback_query(F.data.startswith("edit_category_"))
async def update_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[-1])
    category = db_get_category(category_id)
    chat_id = callback.message.chat.id
    lang = LANG.get(chat_id, "uz")
    if not category:
        await callback.message.answer(translations[lang]["category_not_found"])
        return

    await state.set_state(EditCategoryForm.category_id)
    await state.update_data(category_id=category_id)

    await callback.message.edit_text(translations[lang]["editing_category_prompt"].format(category_name=category.category_name))

    await state.set_state(EditCategoryForm.name)


@admin_router.message(IsAdmin(), EditCategoryForm.name)
async def process_edit_category_name(message: Message, state: FSMContext):
    data = await state.get_data()
    category_id = data["category_id"]
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")

    if message.text.lower() != "skip":
        name = message.text.strip()
        success = db_update_category(category_id, name)
        if success:
            await message.answer(translations[lang]["category_updated_success"])
        else:
            await message.answer(translations[lang]["category_updated_fail"])
    else:
        await message.answer(translations[lang]["category_not_updated"])

    await state.clear()


@admin_router.callback_query(IsAdmin(), F.data.startswith("delete_category_"))
async def confirm_delete_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[-1])
    category = db_get_category(category_id)
    chat_id = callback.message.chat.id
    lang = LANG.get(chat_id, "uz")
    if not category:
        await callback.answer(translations[lang]["category_not_found"])

    await state.set_state(DeleteCategoryForm.category_id)
    await state.update_data(category_id=category_id)

    await callback.message.edit_text(
        translations[lang]["confirm_delete_category_prompt"].format(category_name=category.category_name),
        reply_markup=generate_confirm_delete_keyboard("category", category_id, lang)
    )


@admin_router.callback_query(IsAdmin(), F.data.startswith("confirm_delete_category"))
async def delete_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[-1])
    chat_id = callback.message.chat.id
    lang = LANG.get(chat_id, "uz")
    success = db_delete_category(category_id)
    if success:
        await callback.message.edit_text(translations[lang]["category_deleted_success"])
        await list_categories(callback.message)

    else:
        await callback.message.edit_text(translations[lang]["category_deleted_fail"])
        await list_categories(callback.message)

    await state.clear()


@admin_router.callback_query(IsAdmin(), F.data.startswith("cancel_delete_category"))
async def cancel_delete_category(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    lang = LANG.get(chat_id, "uz")
    await callback.message.edit_text(translations[lang]["category_deletion_canceled"])


@admin_router.callback_query(F.data.startswith("return_to_categories"))
async def return_to_category_list(callback: CallbackQuery, bot: Bot):
    try:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
        await list_categories(callback.message)
    except Exception as e:
        print(f"Error in return_to_category_list {str(e)}")


"""
Admin product management
"""


@admin_router.message(IsAdmin(), Command("addproduct"))
async def add_product_command(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    categories = db_get_all_categories()
    if not categories:
        await message.answer(translations[lang]["no_categories_for_product"])
        return

    await message.answer(
        translations[lang]["select_category_for_product"],
        reply_markup=generate_categories_for_admin(categories)
    )

    await state.set_state(ProductForm.category_id)


@admin_router.callback_query(F.data.startswith("admin_category_"))
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    """process category selection for new product"""
    category_id = int(callback.data.split("_")[-1])
    chat_id = callback.message.chat.id
    lang = LANG.get(chat_id, "uz")
    await state.update_data(category_id=category_id)
    await callback.message.edit_text(translations[lang]["enter_product_name"])
    await state.set_state(ProductForm.name)


@admin_router.message(ProductForm.name)
async def process_product_name(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    await state.update_data(name=message.text.strip())
    await message.answer(translations[lang]["enter_product_description"])
    await state.set_state(ProductForm.description)


@admin_router.message(ProductForm.description)
async def process_product_description(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    await state.update_data(description=message.text.strip())
    await message.answer(translations[lang]["enter_product_price"])
    await state.set_state(ProductForm.price)


@admin_router.message(ProductForm.price)
async def process_product_price(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    try:
        product_price = float(message.text.strip())
        await state.update_data(price=product_price)
        await message.answer(translations[lang]["enter_product_image"])
        await state.set_state(ProductForm.image)
    except ValueError as e:
        await message.answer(translations[lang]["invalid_price_format"])


@admin_router.message(ProductForm.image, F.photo)
async def process_product_image(message: Message, state: FSMContext, bot: Bot):
    """Process product image and add product to database"""
    photo = message.photo[-1]
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path
    download_file = await bot.download_file(file_path)

    image_filename = f"media/{photo.file_id}.jpg"
    os.makedirs("media", exist_ok=True)
    with open(image_filename, "wb") as f:
        f.write(download_file.read())

    await state.update_data(image=image_filename)

    data = await state.get_data()

    success = db_add_product(
        category_id=data["category_id"],
        product_name=data["name"],
        description=data["description"],
        price=data["price"],
        image=data["image"]
    )

    if success:
        await message.answer(translations[lang]["product_added_success"].format(product_name=data['name']))
    else:
        await message.answer(translations[lang]["product_added_fail"])

    await state.clear()


@admin_router.message(IsAdmin(), Command("products"))
async def list_products(message: Message):
    """List all products with management options"""
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    products = db_get_all_products()
    if not products:
        await message.answer(translations[lang]["products_not_found"])
        return

    text = translations[lang]["products_list_title"]
    text += translations[lang]["products_list_instruction"]
    await message.answer(
        text,
        reply_markup=generate_products_for_admin(products)
    )


@admin_router.callback_query(IsAdmin(), F.data.startswith("admin_prod_"))
async def show_product_actions(callback: CallbackQuery):
    """Show actions for selected product"""
    product_id = int(callback.data.split("_")[-1])
    product = db_get_product_by_id(product_id)
    chat_id = callback.message.chat.id
    lang = LANG.get(chat_id, "uz")
    if not product:
        await callback.message.answer(translations[lang]["products_not_found"])
        return

    text = translations[lang]["product_details_text"].format(product_name=product.product_name,
                                                             product_description=product.description,
                                                             product_price=product.price)

    await callback.message.edit_text(
        text,
        reply_markup=generate_edit_product_keyboard(product_id, lang)
    )


@admin_router.callback_query(IsAdmin(), F.data.startswith("edit_product_"))
async def start_edit_product(callback: CallbackQuery, state: FSMContext):
    """Start product editing process"""
    product_id = int(callback.data.split("_")[-1])
    product = db_get_product_by_id(product_id)
    chat_id = callback.message.chat.id
    lang = LANG.get(chat_id, "uz")
    if not product:
        await callback.message.answer(translations[lang]["products_not_found"])
        return

    await state.set_state(EditProductForm.product_id)
    await state.update_data(product_id=product_id)
    text = translations[lang]["editing_product_prompt"].format(product_name=product.product_name)
    await callback.message.edit_text(
        text
    )

    await state.set_state(EditProductForm.name)


@admin_router.message(IsAdmin(), EditProductForm.name)
async def process_edit_name(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    if message.text.lower() != "skip":
        await state.update_data(name=message.text.strip())

    await message.answer(translations[lang]["enter_new_description_prompt"])
    await state.set_state(EditProductForm.description)


@admin_router.message(IsAdmin(), EditProductForm.description)
async def process_edit_description(message: Message, state: FSMContext):
    if message.text.lower() != "skip":
        await state.update_data(description=message.text.strip())
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")

    await message.answer(translations[lang]["enter_new_price_prompt"])
    await state.set_state(EditProductForm.price)


@admin_router.message(IsAdmin(), EditProductForm.price)
async def process_edit_price(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    try:
        if message.text.lower() != "skip":
            new_price = float(message.text.strip())
            await state.update_data(price=new_price)

        await message.answer(translations[lang]["upload_new_image_prompt"])
        await state.set_state(EditProductForm.image)

    except ValueError as e:
        await message.answer(translations[lang]["invalid_price_edit_format"])


@admin_router.message(IsAdmin(), EditProductForm.image, F.photo)
async def process_edit_image_photo(message: Message, state: FSMContext, bot: Bot):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path
    download_file = await bot.download_file(file_path)

    image_filename = f"media/{photo.file_id}.jpg"
    os.makedirs("media", exist_ok=True)
    with open(image_filename, "wb") as f:
        f.write(download_file.read())

    await state.update_data(image=image_filename)
    await update_product(message, state)


@admin_router.message(IsAdmin(), EditProductForm.image)
async def process_edit_image(message: Message, state: FSMContext):
    """Handle skip or invalid input"""
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")
    if message.text and message.text.lower() == "skip":
        print("skip detected for image")
        await update_product(message, state)
    else:
        await message.answer(translations[lang]["send_image_or_skip"])


async def update_product(message: Message, state: FSMContext):
    """Update product in database with current state data"""
    data = await state.get_data()
    product_id = data["product_id"]
    chat_id = message.chat.id
    lang = LANG.get(chat_id, "uz")

    product = db_get_product_by_id(product_id)
    if not product:
        await message.answer(translations[lang]["products_not_found"])
        await state.clear()
        return

    name = data.get("name", product.product_name)
    description = data.get("description", product.description)
    price = data.get("price", product.price)
    image = data.get("image", product.image)

    success = db_update_product(
        product_id=product_id,
        name=name,
        description=description,
        price=price,
        image=image
    )

    if success:
        await message.answer(translations[lang]["product_updated_success"])
    else:
        await message.answer(translations[lang]["product_updated_fail"])

    await state.clear()


@admin_router.callback_query(IsAdmin(), F.data.startswith("delete_product_"))
async def confirm_delete_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[-1])
    product = db_get_product_by_id(product_id)
    chat_id = callback.message.chat.id
    lang = LANG.get(chat_id, "uz")
    if not product:
        await callback.answer(translations[lang]["products_not_found"])
        return

    await state.set_state(DeleteProductForm.product_id)
    await state.update_data(product_id=product_id)

    await callback.message.edit_text(
        translations[lang]["confirm_delete_product_prompt"].format(product_name=product.product_name),
        reply_markup=generate_confirm_delete_keyboard("product", product_id, lang)
    )


@admin_router.callback_query(IsAdmin(), F.data.startswith("confirm_delete_product"))
async def delete_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[-1])
    product = db_get_product_by_id(product_id)
    chat_id = callback.message.chat.id
    lang = LANG.get(chat_id, "uz")
    image_path = product.image
    if os.path.exists(image_path):
        os.remove(image_path)

    success = db_delete_product(product_id)
    if success:
        await callback.message.edit_text(translations[lang]["product_deleted_success"])
    else:
        await callback.message.edit_text(translations[lang]["product_deleted_fail"])

    await state.clear()


@admin_router.callback_query(IsAdmin(), F.data.startswith("cancel_delete_product"))
async def cancel_delete_category(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    lang = LANG.get(chat_id, "uz")
    await callback.message.edit_text(translations[lang]["product_deletion_canceled"])


@admin_router.callback_query(F.data.startswith("return_to_products"))
async def return_to_product_list(callback: CallbackQuery, bot: Bot):
    try:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
        await list_products(callback.message)
    except Exception as e:
        print(f"Error in return_to_products {str(e)}")
