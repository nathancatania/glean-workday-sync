from typing import Any, Literal
import json
import os
import logging
import requests
import csv
from datetime import datetime
from uuid_extensions import uuid7
from utils.config import UploadResult, DataType, GleanApiVersion, get_settings

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(asctime)s: %(message)s', datefmt='%b %d %H:%M:%S %Z')
logger = logging.getLogger(__name__)

def load_mapping(mapping_file: str) -> dict[str, Any]:
    """Load and return the field mapping from a JSON file."""
    try:
        # Mapping file will be located in parent directory so get correct path:
        mapping_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', mapping_file)

        with open(mapping_file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Mapping file '{mapping_file}' not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Error loading mapping file '{mapping_file}'. Could not decode JSON.")
    except Exception as e:
        raise Exception(f"An error occurred loading the mapping file: {e}")

def bulk_upload_entities(data: list[dict[str, Any]], type: Literal['people', 'teams'] = 'people') -> UploadResult:
    """Bulk upload the transformed people/teams data to the Glean Indexing API."""
    warnings = []
    upload_id = uuid7(as_type='str')
    count = 0
    is_first_page = True

    try:
        settings = get_settings()

        # Adjust logging level based on settings
        logger.setLevel(logging.DEBUG if settings.DEBUG_MODE else logging.INFO)

        if not data:
            raise ValueError("No data to upload to Glean API.")
        
        if type not in ['people', 'teams']:
            raise ValueError("Invalid data type for upload of entities to Glean. Must be 'people' or 'teams'.")
        
        api_endpoint = 'bulkindexemployees' if type == 'people' else 'bulkindexteams'
        url = f"https://{settings.GLEAN_BACKEND_DOMAIN}/api/index/{GleanApiVersion.V1.value}/{api_endpoint}"

        headers = {'Authorization': f'Bearer {settings.GLEAN_API_KEY.get_secret_value()}'}

        logger.info(f"Starting upload of {len(data)} records to the Glean API: {url}")
        logger.info(f"Upload ID: {upload_id}")

        for i in range(0, len(data), settings.BATCH_SIZE):
            bulk_data = data[i:i+settings.BATCH_SIZE]
            is_last_page = i + settings.BATCH_SIZE >= len(data)

            payload = {
                "uploadId": upload_id,
                "isFirstPage": is_first_page,
                "isLastPage": is_last_page,
                "forceRestartUpload": is_first_page
            }

            payload['employees' if type == 'people' else 'teams'] = bulk_data

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 400 and "Employees uploaded successfully" in response.text:
                warnings.append(f"Glean API returned 400 on success with warning: {response.text}")
            else:
                response.raise_for_status()

            count += len(bulk_data)
            is_first_page = False

            logger.info(f"Uploaded {count}/{len(data)} records to Glean API.")
            logger.debug(f"API code: {response.status_code}")

        wait_time = "1 hour"

        process_url = f"https://{settings.GLEAN_BACKEND_DOMAIN}/api/index/{GleanApiVersion.V1.value}/processallemployeesandteams"
        process_response = requests.post(process_url, headers=headers)

        if not process_response.ok:
            wait_time = "3 hours"
            logger.warning(f"Request to schedule immediate processing of uploaded data failed (HTTP {process_response.status_code}). Data will be automatically processed after {wait_time}.")
        else:
            logger.info("Immediate processing of uploaded data scheduled successfully.")

    except requests.HTTPError as e:
        error_msgs = {
            409: "Duplicate upload ID. Please try again with a new upload ID.",
            429: "Glean API rate limit exceeded. Please wait a few minutes and try again.",
            500: "The Glean API is currently unavailable. Please try again later.",
            501: "The Glean API is currently unavailable. Please try again later.",
            503: "The Glean API is currently unavailable. Please try again later.",
            400: "The request data was rejected as being invalid or malformed. Please check the data and try again.",
            401: "Unauthorized. Please check that the Glean Indexing API key is valid and has the ENTITIES scope assigned.",
            405: "The Glean API rejected the request as it was not made using a supported method, or to a valid API endpoint. Check the request and try again."
        }
        error_msg = error_msgs.get(e.response.status_code, str(e.response.text))
        logger.debug(f"API response: {e.response.text}")
        raise Exception(f"Upload to Glean failed (HTTP {e.response.status_code}): {error_msg}")

    except Exception as e:
        raise Exception(f"An error occurred uploading data to Glean API: {e}")

    else:
        logger.info(f"Data uploaded successfully to Glean API. Total records uploaded: {count}")
        logger.info(f"Please allow {wait_time} for the data to be visible in the Glean app.")
        return UploadResult(
            success=True,
            records_uploaded=count,
            upload_id=upload_id,
            warnings=warnings,
            timestamp=datetime.now()
        )
    
def create_csv(data: list[dict[str, Any]], output_file: str, mode: str):
    """Create a CSV file containing people or teams data."""
    try:
        if not data:
            raise ValueError(f"No data to write to {mode} CSV.")

        flattened_data = []
        for item in data:
            flattened_item = {}
            for key, value in item.items():
                if key == 'teams' and mode == 'people':
                    continue
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        flattened_item[f'{sub_key}'] = sub_value
                elif isinstance(value, list) and key == 'members':
                    flattened_item[key] = ','.join([member['email'] for member in value])
                else:
                    flattened_item[key] = value
            flattened_data.append(flattened_item)

        fieldnames = flattened_data[0].keys()

        print(f"\n\nFlattened data: {json.dumps(flattened_data)}")
        print(f"\n\nField names: {fieldnames}")
        
        # with open(output_file, 'w', newline='') as csvfile:
        #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        #     writer.writeheader()
        #     for item in flattened_data:
        #         writer.writerow(item)
    
    except ValueError as e:
        raise ValueError(f"Error writing {mode} data to CSV: {e}")
    except Exception as e:
        raise Exception(f"An error occurred writing {mode} data to CSV: {e}")
    else:
        logger.info(f"{mode.capitalize()} data written to {output_file} successfully.")
        return True