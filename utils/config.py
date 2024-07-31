from pydantic import HttpUrl, SecretStr, model_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum
from typing import Optional
from functools import lru_cache
from dataclasses import dataclass
from datetime import datetime
import os
import logging

class AuthType(str, Enum):
    BASIC = 'basic'
    BEARER = 'bearer'

class DataType(str, Enum):
    PEOPLE = 'people'
    TEAMS = 'teams'

class OutputType(str, Enum):
    API = 'api'
    CSV = 'csv'

class TestMode(str, Enum):
    PULL = 'pull'
    PUSH = 'push'

class GleanApiVersion(str, Enum):
    V1 = 'v1'

@dataclass
class UploadResult:
    success: bool
    records_uploaded: int
    upload_id: str
    warnings: list[str]
    timestamp: datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(asctime)s: %(message)s', datefmt='%b %d %H:%M:%S %Z')

class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # Workday settings
    WORKDAY_REPORT_URL: Optional[HttpUrl] = None
    WORKDAY_AUTH_TYPE: AuthType = AuthType.BEARER
    WORKDAY_API_KEY: Optional[SecretStr] = None
    WORKDAY_USERNAME: Optional[str] = None
    WORKDAY_PASSWORD: Optional[SecretStr] = None

    # Glean settings
    GLEAN_BACKEND_DOMAIN: Optional[str] = None
    GLEAN_API_KEY: Optional[SecretStr] = None

    # Application settings
    FIELD_MAPPING_FILE: str = 'mapping.json'
    OUTPUT_TYPE: OutputType = OutputType.API
    DATA_TYPE: DataType = DataType.PEOPLE
    BATCH_SIZE: int = 250

    # Debug and test settings
    DEBUG_MODE: bool = False
    TEST_MODE: Optional[TestMode] = None
    TEST_DATA_FILE: Optional[str] = None

    @model_validator(mode='after')
    def validate_settings(self):
        if self.TEST_MODE == TestMode.PUSH:
            self._validate_push_mode()
        elif self.TEST_MODE == TestMode.PULL:
            self._validate_pull_mode()
        else:
            self._validate_normal_mode()
        return self

    def _validate_push_mode(self):
        if not self.TEST_DATA_FILE:
            raise ValueError('TEST_DATA_FILE is required when TEST_MODE is push.')
        self._validate_glean_settings('in push test mode')

    def _validate_pull_mode(self):
        self._validate_workday_settings('in pull test mode')

    def _validate_normal_mode(self):
        self._validate_workday_settings()
        self._validate_glean_settings()

    def _validate_workday_settings(self, mode_description: str = ''):
        suffix = f' {mode_description}' if mode_description else ''
        if not self.WORKDAY_REPORT_URL:
            raise ValueError(f'WORKDAY_REPORT_URL is required{suffix}.', error_type='value_error')
        if self.WORKDAY_AUTH_TYPE == AuthType.BASIC:
            if not self.WORKDAY_USERNAME or not self.WORKDAY_PASSWORD:
                raise ValueError(f'Username and password are required for Workday basic authentication{suffix}.', error_type='value_error')
        elif self.WORKDAY_AUTH_TYPE == AuthType.BEARER:
            if not self.WORKDAY_API_KEY:
                raise ValueError(f'Workday API key is required for bearer authentication{suffix}.', error_type='value_error')

    def _validate_glean_settings(self, mode_description: str = ''):
        suffix = f' {mode_description}' if mode_description else ''
        if not self.GLEAN_BACKEND_DOMAIN or not self.GLEAN_API_KEY:
            raise ValueError(f'GLEAN_BACKEND_DOMAIN and GLEAN_API_KEY are required{suffix}', error_type='value_error')

@lru_cache
def get_settings():
    try:
        return Settings()
    except ValidationError as e:
        for error in e.errors():
            if 'ctx' in error and 'error' in error['ctx']:
                logger.error(error['ctx']['error'])
            else:
                logger.error(error['msg'])
        raise ConfigurationError("Settings validation failed. Please check the configuration.")

class ConfigurationError(Exception):
    """Custom exception for configuration errors."""
    pass