from slugify import slugify
import textwrap


def format_cart_item(cart_item):
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


def format_order(cart, delivery_cost):
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


def format_product(product_details):
    """Reformat product details from dictionary to format requested by API.

    Args:
        product_details: product details dictionary

    Returns:
        formatted product data for API
    """
    slugified_name = slugify(product_details['name'])
    nutritional_value = product_details['food_value']

    description = textwrap.dedent(
        f'''\
        {product_details['description']}

        Пищевая ценность:
        Жиры: {nutritional_value['fats']}
        Протеины: {nutritional_value['proteins']}
        Углеводы: {nutritional_value['carbohydrates']}
        Ккал: {nutritional_value['kiloCalories']}
        Вес: {nutritional_value['weight']}
        '''
    )

    data = {
        'data': {
            'type': 'product',
            'name': product_details['name'],
            'slug': slugified_name,
            'sku': f'{slugified_name}-{product_details["id"]}',
            'description': description,
            'manage_stock': False,
            'price': [
                {
                    'amount': product_details['price'],
                    'currency': 'RUB',
                    'includes_tax': True,
                }
            ],
            'status': 'live',
            'commodity_type': 'physical',
        },
    }

    return data


def format_delivery_options(distance, pizzeria_address, delivery_cost):
    if distance > 20:
        return textwrap.dedent(
            f"""
            Простите, но так далеко мы пиццу не доставляем. Ближайшая
            пиццерия находится в {distance:.1f} километрах от Вас! Возможен
            только самовывоз.
            """
        )

    if distance <= 0.5:
        return textwrap.dedent(
            f"""
            Может, заберете пиццу из нашей пиццерии неподалёку?
            Она всего в {round(distance * 1000)} метрах от вас!
            Вот её адрес: {pizzeria_address}.

            Также возможен вариант бесплатной доставки.
            """
        )

    if distance <= 5:
        return textwrap.dedent(
            f"""
            Похоже, придётся ехать до Вас на самокате. Доставка
            будет стоить {delivery_cost} рублей. Доставляем или самовывоз?
            """
        )

    return textwrap.dedent(
        f"""
        Похоже, придётся ехать до Вас на авто. Доставка будет
        стоить {delivery_cost} рублей. Доставляем или самовывоз?
        """
    )
