
def text_for_caption(product_name: str, price: int, description: str) -> str:
    text = f"<b>{product_name}</b> \n\n"
    text += f"<b>Description</b> - {description}\n"
    text += f"Price: <b>{price} sum</b>"

    return text
