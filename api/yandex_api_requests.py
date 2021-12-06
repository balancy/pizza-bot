from typing import Optional

import requests


def fetch_coordinates(apikey: str, address: str) -> Optional[tuple]:
    """Fetch coordinates with yandex api.

    Args:
        apikey: yandex api token
        address: address to fetch coordinates for

    Returns:
        tuple containing coordinates or None
    """

    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(
        base_url,
        params={
            "geocode": address,
            "apikey": apikey,
            "format": "json",
        },
    )
    response.raise_for_status()

    found_places = response.json()['response']['GeoObjectCollection'][
        'featureMember'
    ]

    if not found_places:
        return

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split()

    return (lat, lon)
