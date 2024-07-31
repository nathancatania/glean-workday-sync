from typing import Any
import logging
import requests
import time
from utils.config import get_settings, AuthType

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(asctime)s: %(message)s', datefmt='%b %d %H:%M:%S %Z')
logger = logging.getLogger(__name__)

def get_report_data() -> dict[str, Any]:
    """Fetch and return data from the Workday Report."""
    try:
        settings = get_settings()

        if settings.WORKDAY_AUTH_TYPE == AuthType.BASIC:
            response = requests.get(
                settings.WORKDAY_REPORT_URL, 
                auth=(settings.WORKDAY_USERNAME, settings.WORKDAY_PASSWORD.get_secret_value())
            )
        else:  # Bearer authentication
            response = requests.get(
                settings.WORKDAY_REPORT_URL, 
                headers={'Authorization': f'Bearer {settings.WORKDAY_API_KEY.get_secret_value()}'}
            )
        
        response.raise_for_status()
        return response.json()
    
    except requests.HTTPError as e:
        error_msgs = {
            429: "Workday API rate limit exceeded. Skipping this run.",
            500: "The Workday endpoint is currently unavailable. Please try again later.",
            501: "The Workday endpoint is currently unavailable. Please try again later.",
            503: "The Workday endpoint is currently unavailable. Please try again later.",
            400: "Invalid request. Please check the request data and try again.",
            401: "Unauthorized request. Please check that the credentials or API key used are valid and try again."
        }
        error_msg = error_msgs.get(e.response.status_code, str(e.response.text))
        logger.debug(f"Workday API response ({e.response.status_code}): {e.response.text}")
        raise Exception(f"Fetching the Workday data failed (HTTP {e.response.status_code}): {error_msg}")

    except Exception as e:
        raise Exception(f"An error occurred fetching the Workday report: {e}")
    
def transform_teams(input_data: list[dict[str, Any]], mapping: dict[str, Any]) -> list[dict[str, Any]]:
    """Transform and return teams data."""
    teams = {}
    team_field = mapping['teams'][0]['__sourceField']
    team_name_key = mapping['teams'][0]['name']
    team_id_key = mapping['teams'][0]['id']
    email_key = mapping['email']

    for item in input_data:
        email = item.get(email_key)
        for team in item.get(team_field, []):
            team_id = team.get(team_id_key)
            if team_id:
                if team_id not in teams:
                    teams[team_id] = {
                        'id': team_id,
                        'name': team.get(team_name_key),
                        'members': []
                    }
                    for key, value in mapping['teams'][0].items():
                        if not key.startswith('__') and key not in ['id', 'name']:
                            teams[team_id][key] = team.get(value)
                
                teams[team_id]['members'].append(dict(email=email))

    return list(teams.values())

def transform_people(input_data: list[dict[str, Any]], mapping: dict[str, Any]) -> list[dict[str, Any]]:
    """Transform and return people data."""
    transformed_data = []
    all_additional_fields = set()
    
    # First pass: collect all additional fields
    for item in input_data:
        for field in mapping.get('additionalFields', []):
            if field in item:
                all_additional_fields.add(field)
    
    for item in input_data:
        transformed_item = {}
        social_networks = []
        additional_fields = []

        for api_key, customer_key in mapping.items():
            if api_key == 'additionalFields':
                continue  # We'll handle this separately
            elif api_key.endswith('Url') and api_key not in ['photoUrl', 'profileUrl']:
                process_social_network(api_key, customer_key, item, social_networks)
            elif isinstance(customer_key, dict):
                transformed_item[api_key] = process_structured_field(item, customer_key)
            elif isinstance(customer_key, list):
                transformed_item[api_key] = process_list_field(item, customer_key)
            else:
                transformed_item[api_key] = item.get(customer_key)

        # Handle additional fields
        for field in all_additional_fields:
            value = item.get(field)
            if value:
                if not isinstance(value, list):
                    value = [str(value)]
                additional_fields.append({
                    'key': field,
                    'value': value
                })

        transformed_item['additionalFields'] = additional_fields

        handle_missing_name(transformed_item)
        process_status(transformed_item)
        process_type(transformed_item)

        if social_networks:
            transformed_item['socialNetworks'] = social_networks

        transformed_data.append(transformed_item)

    return transformed_data

def process_social_network(api_key: str, customer_key: str, item: dict[str, Any], social_networks: list[dict[str, str]]):
    """Process and add social network data."""
    network_name = api_key[:-3].lower()
    profile_name = {'linkedin': 'LinkedIn', 'whatsapp': 'WhatsApp', 'imessage': 'iMessage'}.get(network_name, network_name.title())
    url = item.get(customer_key)
    if url:
        social_networks.append({
            'name': network_name,
            'profileName': profile_name,
            'profileUrl': url
        })

def process_list_field(item: dict[str, Any], customer_key: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Process and return list field data."""
    source_field = customer_key[0]['__sourceField']
    source_list = item.get(source_field, [])
    if isinstance(source_list, list):
        return [{sub_api_key: source_item.get(sub_customer_key) 
                 for sub_api_key, sub_customer_key in customer_key[0].items() 
                 if not sub_api_key.startswith('__')} 
                for source_item in source_list]
    else:
        return []

def process_structured_field(item: dict[str, Any], customer_key: dict[str, str]) -> dict[str, Any]:
    """Process and return structured field data."""
    return {sub_api_key: item.get(sub_customer_key) 
            for sub_api_key, sub_customer_key in customer_key.items()}

def handle_missing_name(transformed_item: dict[str, Any]):
    """Handle missing name data."""
    if not transformed_item.get('firstName') and not transformed_item.get('lastName'):
        name_parts = transformed_item.get('preferredName', '').split()
        if name_parts:
            transformed_item['firstName'] = name_parts[0]
            transformed_item['lastName'] = ' '.join(name_parts[1:]) or ' '

def process_status(transformed_item: dict[str, Any]):
    """Process and set employee status."""
    hire_date = transformed_item.get('startDate')
    end_date = transformed_item.get('endDate')
    current_date = time.strftime('%Y-%m-%d')
    
    if end_date and end_date < current_date:
        transformed_item['status'] = 'EX'
    elif hire_date:
        transformed_item['status'] = 'FUTURE' if hire_date > current_date else 'CURRENT'

def process_type(transformed_item: dict[str, Any]):
    """Process and set employee type."""
    type_value = transformed_item.get('type', 'FULL_TIME')
    if type_value is not None:
        type_value = type_value.replace('-', '_').replace(' ', '_').upper()
        if type_value in ['FULL_TIME', 'CONTRACTOR', 'NON_EMPLOYEE']:
            transformed_item['type'] = type_value
        else:
            logger.warning(f"Invalid 'type' value '{type_value}' for employee {transformed_item.get('email')}. Skipping for this employee.")