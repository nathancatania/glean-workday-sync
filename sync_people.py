import json
import logging
import sys
from utils.config import get_settings, ConfigurationError, DataType, TestMode, OutputType
from utils import workday
from utils import glean
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(asctime)s: %(message)s', datefmt='%b %d %H:%M:%S %Z')
logger = logging.getLogger(__name__)


def main(mode: DataType = DataType.PEOPLE):
    """
    Synchronize people/employee/teams data from Workday to Glean.

    This function fetches employee data from a Workday Report, transforms it to the format required by Glean, and then either exports it to CSV files
    or pushes it to the Glean API in bulk.

    The function reads settings from environment variables and uses the field mapping file to transform the data from the format
    recieved from Workday to the format expected by the Glean API.

    The function also supports test modes, where the data is:
    1. Pulled from Workday, but not pushed to Glean API (pull test mode).
    2. Loaded from a local file and pushed to Glean API (push test mode).

    Certain environment variables must be set for the function to work correctly. See the README for more information:
    - WORKDAY_REPORT_URL : URL of the Workday report to fetch data from in JSON format.
    - WORKDAY_AUTH_TYPE : Type of authentication to use with the Workday API ('basic' or 'bearer').
    - WORKDAY_API_KEY or WORKDAY_USERNAME and WORKDAY_PASSWORD : Credentials to authenticate with the Workday API.
    - GLEAN_BACKEND_DOMAIN : Domain of the Glean API backend, e.g. 'mytenant-be.glean.com'.
    - GLEAN_API_KEY : API key to authenticate with the Glean Indexing API. Must be scoped to 'ENTITIES'.
    
    You will also need to customize the field mapping file (mapping.json) to map the fields from Workday to the fields expected by the Glean API.
    See the README for more information.

    Run the script `python sync_people.py` to synchronize people data from Workday to Glean.
    Run the script with the --teamsonly flag to only process teams data and memberships (no employee data).
    """
    try:
        # Load settings from environment variables
        settings = get_settings()

        # Adjust logging level based on settings
        logger.setLevel(logging.DEBUG if settings.DEBUG_MODE else logging.INFO)
        
        # Set data type to 'teams' if requested via cli argument
        if mode == DataType.TEAMS:
            settings.DATA_TYPE = DataType.TEAMS

        # Log the data type that will be processed.
        if settings.DATA_TYPE == DataType.TEAMS:
            logger.debug("Data type set to 'teams'. Only processing teams data and memberships.")

        # Warn if test mode is enabled
        if settings.TEST_MODE:
            if settings.TEST_MODE == TestMode.PULL:
                logger.warning("Pull test mode enabled. Data will be pulled from Workday but not pushed to Glean API.")
            elif settings.TEST_MODE == TestMode.PUSH:
                logger.warning("Push test mode enabled. Loading data from local file and pushing to Glean API.")

        # Load the field mapping file (Glean API <-> Workday field mapping)
        logger.info(f"Loading mapping file: {settings.FIELD_MAPPING_FILE}")
        mapping = glean.load_mapping(settings.FIELD_MAPPING_FILE)

        # Fetch the initial data
        if settings.TEST_MODE == TestMode.PUSH:
            # Push test mode == Test Glean API only, so load data from local file
            logger.info(f"Loading test data from: {settings.TEST_DATA_FILE}")
            with open(f'{settings.TEST_DATA_FILE}', 'r') as f:
                response_data = json.load(f)
            logger.debug(f"Test data loaded: {json.dumps(response_data)}")
        else:
            # Fetch data from Workday
            logger.info(f"Fetching data from Workday: {settings.WORKDAY_REPORT_URL}")
            response_data = workday.get_report_data()
            #logger.debug(f"Workday data fetched: {json.dumps(response_data)}")

        # Transform the Workday data to Glean API format using the field mapping
        logger.info("Transforming Workday data to Glean API format...")
        if settings.DATA_TYPE == DataType.TEAMS:
            transformed_data = workday.transform_teams(response_data["Report_Entry"], mapping)
        else:
            transformed_data = workday.transform_people(response_data["Report_Entry"], mapping)
        logger.debug(f"Transformed data: {json.dumps(transformed_data)}")

        # Export the transformed data to CSV files or push to Glean API
        if settings.OUTPUT_TYPE == OutputType.CSV:
            # CSV output mode
            logger.info("Exporting data to CSV files...")
            glean.create_csv(transformed_data, 'people.csv' if settings.DATA_TYPE == DataType.PEOPLE else 'teams.csv', settings.DATA_TYPE.value)
        elif settings.TEST_MODE != TestMode.PULL:
            # Push to Glean API
            # Skipped if in pull test mode (testing Workday data fetch only)
            result = glean.bulk_upload_entities(transformed_data, type=settings.DATA_TYPE)
            if result.warnings:
                logger.warning("The following warnings were encountered during the upload:")
                for warning in result.warnings:
                    logger.warning(f" - {warning}")

    except ConfigurationError as e:
        logger.error(str(e))
        exit(1)
    
    except Exception as e:
        logger.error(f"{e}")
        sys.exit(1)

    else:
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--teamsonly", action="store_true", help="Only process teams data and memberships.")
    args = parser.parse_args()

    main(mode=DataType.TEAMS if args.teamsonly else DataType.PEOPLE)