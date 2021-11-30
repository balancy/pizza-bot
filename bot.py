import json

if __name__ == '__main__':
    with open("addresses.json", "r") as addresses_file:
        addresses = json.load(addresses_file)

    with open("menu.json", "r") as menu_file:
        menu = json.load(menu_file)

    print(addresses)
    print(menu)
