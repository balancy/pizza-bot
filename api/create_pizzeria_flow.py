import os

from dotenv import load_dotenv

from api.moltin_requests import (
    create_flow,
    create_flow_field,
    fetch_auth_token,
)

ADDRESSES_FILE = 'api/addresses.json'


if __name__ == '__main__':
    load_dotenv()

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    auth_token = fetch_auth_token(client_id, client_secret)['access_token']

    flow_details = create_flow(
        token=auth_token,
        name='Pizzeria',
        description='Storing pizzeria places',
    )

    flow_id = flow_details['data']['id']
    flow_fields_details = {
        'Address': ('string', 'Pizzeria full address'),
        'Alias': ('string', 'Pizzeria alias name'),
        'Longitude': ('float', 'Pizzeria longitude'),
        'Latitude': ('float', 'Pizzeria latitude'),
    }

    for field, (field_type, description) in flow_fields_details.items():
        create_flow_field(
            auth_token,
            name=field,
            description=description,
            field_type=field_type,
            flow_id=flow_id,
        )
