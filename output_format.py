import textwrap


def format_cart_item_for_display(cart_item):
    """Transfrom cart item dicionary to formatted string

    Args:
        cart_item: cart item dicionary

    Returns:
        formatted string
    """
    name = cart_item['name']
    formatted_price = cart_item['meta']['display_price']['without_tax']
    unit_price = formatted_price['unit']['amount']
    position_price = formatted_price['value']['amount']
    quantity = cart_item['quantity']

    return textwrap.dedent(
        f"""\
        <strong>{name}</strong>
        Цена: {unit_price} рублей за штуку
        Штук в корзине: {quantity} на сумму {position_price} рублей

        """
    )


def format_order_for_deliveryman(cart, delivery_cost):
    """Format order details for deliveryman

    Args:
        cart (dictionary): client current cart as order details
        deliver_cost: cost of delivery

    Returns:
        str: order details in formatted form
    """
    cart_positions = ''.join(
        '{}: {} шт\n'.format(cart_item['name'], cart_item['quantity'])
        for cart_item in cart['data']
    )
    cart_positions = '{}Плата за доставку: {} рублей\n'.format(
        cart_positions,
        delivery_cost,
    )

    total_amount = cart['meta']['display_price']['without_tax']['amount']
    total_amount += delivery_cost

    return '{}\n<strong>Всего к оплате: {} рублей</strong>'.format(
        cart_positions,
        total_amount,
    )


def format_order_details_for_invoice(cart):
    """Format order details for payment invoice

    Args:
        cart (dictionary): client current cart as order details

    Returns:
        str: order details in formatted form
    """
    return ''.join(
        '{}: {} шт; '.format(cart_item['name'], cart_item['quantity'])
        for cart_item in cart['data']
    )
