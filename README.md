# PIZZA SHOP BOT

![gif](https://s10.gifyu.com/images/pizza_bot.gif)

App represents telegram bot for customers of imagined "Pizza Shop". "Pizza shop" is a test online shop with data hosted on [Elasticpath](https://www.elasticpath.com/) e-commerce platform.

Bot allows to user to:
- list all available items
- go into product details
- add them to the cart
- delete items from the cart
- find the nearest pizzeria according to provided address or coordinates
- calculate delivery cost based on the distance to the nearest pizzeria
- process to checkout with the test payment method

Link to telegram bot: [Bot](https://t.me/devman_pizzza_bot)

## Install

At least Python 3.8 and Git should be already installed.

1. Clone the repository
```
git clone https://github.com/balancy/pizza-bot
```

2. Go inside cloned repository, create and activate virtal environment:
```console
python -m venv .venv
source .venv/bin/activate (.venv\scripts\activate for Windows)
```

3. Install dependecies:
```console
pip install -r requirements.txt
```

4. Rename `.env.example` to `.env` and define your environment variables

- `CLIENT_ID` - client id of your [elasticpath](https://www.elasticpath.com/) account
- `CLIENT_SECRET` - client secret of your [elasticpath](https://www.elasticpath.com/) account
- `TG_BOT_TOKEN` - token of your telegram pizza shop bot. Could be acquired via [BotFather](https://t.me/BotFather).
- `YANDEX_API_TOKEN` - token of your yandex account. Could by acquired via [yandex](https://developer.tech.yandex.ru/services/).
- `PAYMENT_PROVIDER_TOKEN` - token of payment provider for your telegram bot. Could be acquired via [BotFather](https://t.me/BotFather).

## Launch bot

```console
python bot.py
```

## NOTES

- `Test card` `4242 4242 4242 4242`