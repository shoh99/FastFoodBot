from database.utils import db_get_all_product_inside_finally_cart


def text_for_caption(product_name: str, price: int, description: str) -> str:
    text = f"<b>{product_name}</b> \n\n"
    text += f"<b>Description</b> - {description}\n"
    text += f"Price: <b>{price} sum</b>"

    return text


def count_products_from_cart(chat_id: int, user_text: str):
    products = db_get_all_product_inside_finally_cart(chat_id)

    text = f"<b>{user_text}</b> \n\n"
    total_price = total_products = count = 0

    for product in products:
        count += 1
        total_price += product.final_price
        total_products += product.quantity
        text += f"{count}. {product.product_name}\n Quantity: {product.quantity} \n Price: {product.final_price} \n\n"

    text += f"Total number of products: {total_products} \nTotal price inside cart: {total_price}"
    return text, products


def count_products_for_purchase(chat_id: int):
    products = db_get_all_product_inside_finally_cart(chat_id)

    text = f"Purchase cheque \n\n"
    total_price = total_products = count = 0

    for product in products:
        total_price += product.final_price
        total_products += 1

    text += f"Total products: {total_products} \n" \
            f"Total price: {total_price}"

    content = (text, total_price)
    return content
