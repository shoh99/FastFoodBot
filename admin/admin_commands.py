import asyncio
import os

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from os import getenv
from dotenv import load_dotenv
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
    try:
        await message.answer(
            "🔐 <b>Admin Panel</b>\n\n"
            "Available commands:\n"
            "/addcategory - Add new category\n"
            "/addproduct - Add new product\n"
            "/categories - View and manage categories\n"
            "/products - View and manage products"
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

    await state.set_state(CategoryForm.name)
    await message.answer("Please enter the name of the new category:")


@admin_router.message(IsAdmin(), CategoryForm.name)
async def process_category_name(message: Message, state: FSMContext):
    category_name = message.text.strip()

    success = db_add_category(category_name)
    if success:
        await message.answer(f"✅Category '{category_name}' has been added successfully!")
    else:
        await message.answer(f"❌Failed to add category. It might already exist.")

    await state.clear()


@admin_router.message(IsAdmin(), Command("categories"))
async def list_categories(message: Message):
    """List all categories with management options"""
    categories = db_get_all_categories()
    if not categories:
        await message.answer("No categories found.")
        return

    text = "📋 <b>Categories</b>\n\n"
    text += "Select category to edit or delete"

    await message.answer(
        text,
        reply_markup=generate_categories_for_admin_edit(categories)
    )


@admin_router.callback_query(F.data.startswith("admin_category_edit_"))
async def manage_selected_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[-1])
    category = db_get_category(category_id)

    if not category:
        await callback.message.answer("Category not found")

    text = f"Category Name: <b>{category.category_name}</b>\n"
    await callback.message.edit_text(text, reply_markup=generate_edit_category_keyboard(category_id))


@admin_router.callback_query(F.data.startswith("edit_category_"))
async def update_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[-1])
    category = db_get_category(category_id)

    if not category:
        await callback.message.answer("Category not found")

    await state.set_state(EditCategoryForm.category_id)
    await state.update_data(category_id=category_id)

    await callback.message.edit_text(f"Editing category: {category.category_name}\n"
                                     f"Enter new name (or send 'skip' to keep current)")

    await state.set_state(EditCategoryForm.name)


@admin_router.message(IsAdmin(), EditCategoryForm.name)
async def process_edit_category_name(message: Message, state: FSMContext):
    if message.text.lower() != "skip":
        data = await state.get_data()
        category_id = data["category_id"]
        name = message.text.strip()
        success = db_update_category(category_id, name)

        if success:
            await message.answer("✅ Category has been updated successfully!")
        else:
            await message.answer("❌ Failed to update category.")

        await state.clear()


@admin_router.callback_query(IsAdmin(), F.data.startswith("delete_category_"))
async def confirm_delete_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[-1])
    category = db_get_category(category_id)

    if not category:
        await callback.answer("Category not found")

    await state.set_state(DeleteCategoryForm.category_id)
    await state.update_data(category_id=category_id)

    await callback.message.edit_text(
        f"⚠️ Are you sure you want to delete category: {category.category_name}",
        reply_markup=generate_confirm_delete_keyboard("category", category_id)
    )

@admin_router.callback_query(IsAdmin(), F.data.startswith("confirm_delete_category"))
async def delete_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[-1])
    success = db_delete_category(category_id)
    if success:
        await callback.message.edit_text("✅ Category has been deleted successfully!")
    else:
        await callback.message.edit_text("Failed to delete category.")

    await state.clear()


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
    categories = db_get_all_categories()
    if not categories:
        await message.answer("❌ No categories found. Please add a category first with /addcategory")
        return

    await message.answer(
        "Select a category for the new product:",
        reply_markup=generate_categories_for_admin(categories)
    )

    await state.set_state(ProductForm.category_id)


@admin_router.callback_query(F.data.startswith("admin_category_"))
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    """process category selection for new product"""
    category_id = int(callback.data.split("_")[-1])

    await state.update_data(category_id=category_id)
    await callback.message.edit_text("Enter product name:")
    await state.set_state(ProductForm.name)


@admin_router.message(ProductForm.name)
async def process_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Enter product description:")
    await state.set_state(ProductForm.description)


@admin_router.message(ProductForm.description)
async def process_product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await message.answer("Enter product price")
    await state.set_state(ProductForm.price)


@admin_router.message(ProductForm.price)
async def process_product_price(message: Message, state: FSMContext):
    try:
        product_price = float(message.text.strip())
        await state.update_data(price=product_price)
        await message.answer("Enter product image")
        await state.set_state(ProductForm.image)
    except ValueError as e:
        await message.answer("X Invalid price. Please enter number. (ex: 25.599)")


@admin_router.message(ProductForm.image, F.photo)
async def process_product_image(message: Message, state: FSMContext, bot: Bot):
    """Process product image and add product to database"""
    photo = message.photo[-1]

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
        await message.answer(f"✅ Product: '{data['name']}' has been added successfully")
    else:
        await message.answer(f"X Failed to add product. It might already exist.")

    await state.clear()


@admin_router.message(IsAdmin(), Command("products"))
async def list_products(message: Message):
    """List all products with management options"""

    products = db_get_all_products()

    await message.answer(
        "📋 <b>Products</b>\n\n"
        "Select a product edit or delete: ",
        reply_markup=generate_products_for_admin(products)
    )


@admin_router.callback_query(IsAdmin(), F.data.startswith("admin_prod_"))
async def show_product_actions(callback: CallbackQuery):
    """Show actions for selected product"""
    product_id = int(callback.data.split("_")[-1])
    product = db_get_product_by_id(product_id)

    if not product:
        await callback.answer("Product not found")
        return

    text = f"<b>{product.product_name}</b>\n"
    text += f"Description: {product.description}"
    text += f"Price: {product.price}"

    await callback.message.edit_text(
        text,
        reply_markup=generate_edit_product_keyboard(product_id)
    )


@admin_router.callback_query(IsAdmin(), F.data.startswith("edit_product_"))
async def start_edit_product(callback: CallbackQuery, state: FSMContext):
    """Start product editing process"""
    product_id = int(callback.data.split("_")[-1])
    product = db_get_product_by_id(product_id)

    if not product:
        await callback.answer("Product not found")
        return

    await state.set_state(EditProductForm.product_id)
    await state.update_data(product_id=product_id)

    await callback.message.edit_text(
        f"Editing product: {product.product_name}\n"
        f"Enter new name (or send 'skip' to keep current):"
    )

    await state.set_state(EditProductForm.name)


@admin_router.message(IsAdmin(), EditProductForm.name)
async def process_edit_name(message: Message, state: FSMContext):
    if message.text.lower() != "skip":
        await state.update_data(name=message.text.strip())

    await message.answer("Enter new description (or send 'skip'):")
    await state.set_state(EditProductForm.description)


@admin_router.message(IsAdmin(), EditProductForm.description)
async def process_edit_description(message: Message, state: FSMContext):
    if message.text.lower() != "skip":
        await state.update_data(description=message.text.strip())

    await message.answer("Enter new price (or send 'skip'):")
    await state.set_state(EditProductForm.price)


@admin_router.message(IsAdmin(), EditProductForm.price)
async def process_edit_price(message: Message, state: FSMContext):
    try:
        if message.text.lower() != "skip":
            new_price = float(message.text.strip())
            await state.update_data(price=new_price)

        await message.answer("Upload new image (or send 'skip'):")
        await state.set_state(EditProductForm.image)

    except ValueError as e:
        await message.answer("X Invalid price. Please enter number. (ex: 25.599)")


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
    if message.text and message.text.lower() == "skip":
        await update_product(message, state)
    else:
        await message.answer("X Please send an image or type 'skip' to keep the current one:")


async def update_product(message: Message, state: FSMContext):
    """Update product in database with current state data"""
    data = await state.get_data()
    product_id = data["product_id"]

    product = db_get_product_by_id(product_id)
    if not product:
        await message.answer("❌ Product not found.")
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
        await message.answer("✅ Product has been updated successfully!")
    else:
        await message.answer("❌ Failed to update product.")

    await state.clear()


@admin_router.callback_query(IsAdmin(), F.data.startswith("delete_product_"))
async def confirm_delete_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[-1])
    product = db_get_product_by_id(product_id)

    if not product:
        await callback.answer("Product not found")
        return

    await state.set_state(DeleteProductForm.product_id)
    await state.update_data(product_id=product_id)

    await callback.message.edit_text(
        f"⚠️ Are you sure you want to delete product: {product.product_name}",
        reply_markup=generate_confirm_delete_keyboard("product", product_id)
    )


@admin_router.callback_query(IsAdmin(), F.data.startswith("confirm_delete_product"))
async def delete_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[-1])
    product = db_get_product_by_id(product_id)
    image_path = product.image
    if os.path.exists(image_path):
        os.remove(image_path)

    success = db_delete_product(product_id)
    if success:
        await callback.message.edit_text("✅ Product has been deleted successfully!")
    else:
        await callback.message.edit_text("Failed to delete product.")

    await state.clear()


@admin_router.callback_query(IsAdmin(), F.data.startswith("cancel_delete"))
async def cancel_delete(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Product Deletion Canceled")


@admin_router.callback_query(F.data.startswith("return_to_products"))
async def return_to_product_list(callback: CallbackQuery, bot: Bot):
    try:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
        await list_products(callback.message)
    except Exception as e:
        print(f"Error in return_to_products {str(e)}")
