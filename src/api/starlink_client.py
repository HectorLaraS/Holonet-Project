"""
Holonet

Starlink API Client
"""

from __future__ import annotations

import requests

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StarlinkClient:
    """
    Client for Starlink Public APIs.
    """

    def __init__(self, access_token: str):

        self.base_url = settings.api_base_url
        self.timeout = settings.timeout

        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def get_products(self) -> dict:
        """
        Retrieves the Starlink Products catalog.
        """

        logger.info(
            "Retrieving Starlink products..."
        )

        response = requests.get(
            f"{self.base_url}/api/public/v2/products",
            headers=self.headers,
            timeout=self.timeout
        )

        response.raise_for_status()

        logger.info(
            "Products retrieved successfully."
        )

        return response.json()
    
    def get_usage(
        self,
        service_line_numbers: list[str] | None = None,
        previous_billing_cycles: int = 1,
        active_service_lines_only: bool = True,
        page: int = 0,
        limit: int = 50
    ) -> dict:
        """
        Retrieves usage information.
        """

        logger.info(
            "Retrieving Starlink usage..."
        )

        body = {
            "serviceLineNumbers": service_line_numbers or [],
            "previousBillingCycles": previous_billing_cycles,
            "activeServiceLinesOnly": active_service_lines_only
        }

        response = requests.post(
            f"{self.base_url}/api/public/v2/data-usage/query?page={page}&limit={limit}",
            headers=self.headers,
            json=body,
            timeout=self.timeout
        )

        response.raise_for_status()

        logger.info(
            "Usage retrieved successfully."
        )

        return response.json()
    
    def get_service_lines(self) -> dict:
        """
        Retrieves all Service Lines.
        """

        logger.info(
            "Retrieving Service Lines..."
        )

        response = requests.get(
            f"{self.base_url}/api/public/v2/service-lines",
            headers=self.headers,
            timeout=self.timeout
        )

        response.raise_for_status()

        logger.info(
            "Service Lines retrieved successfully."
        )

        return response.json()
    
    def get_service_line(
        self,
        service_line_number: str
    ) -> dict:
        """
        Retrieves a single Service Line.
        """

        logger.info(
            f"Retrieving Service Line {service_line_number}..."
        )

        response = requests.get(
            f"{self.base_url}/api/public/v2/service-lines/{service_line_number}",
            headers=self.headers,
            timeout=self.timeout
        )

        response.raise_for_status()

        logger.info(
            "Service Line retrieved successfully."
        )

        return response.json()