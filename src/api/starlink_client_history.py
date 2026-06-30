"""
Holonet

History Report

Experimental Version

------------------------------------------------------------------------------
This module is intentionally independent from the production report.

The goal is to validate historical Starlink Billing information without
modifying the current reporting workflow.

Once validated, this module may be refactored or merged into the production
implementation.
------------------------------------------------------------------------------
"""

from __future__ import annotations

import requests

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StarlinkHistoryClient:
    """
    Client for Starlink Public APIs (History Report).
    """

    def __init__(self, access_token: str):

        self.base_url = settings.api_base_url
        self.timeout = settings.timeout

        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def get_usage(
        self,
        service_line_numbers: list[str] | None = None,
        previous_billing_cycles: int = 3,
        active_service_lines_only: bool = True,
        page: int = 0,
        limit: int = 50
    ) -> dict:
        """
        Retrieves historical usage information.
        """

        logger.info(
            "Retrieving Starlink historical usage..."
        )

        body = {
            "serviceLineNumbers": service_line_numbers or [],
            "previousBillingCycles": previous_billing_cycles,
            "activeServiceLinesOnly": active_service_lines_only
        }

        response = requests.post(
            (
                f"{self.base_url}"
                f"/api/public/v2/data-usage/query"
                f"?page={page}&limit={limit}"
            ),
            headers=self.headers,
            json=body,
            timeout=self.timeout
        )

        #
        # Better error reporting
        #

        if not response.ok:

            logger.error(
                f"HTTP {response.status_code}"
            )

            logger.error(
                response.text
            )

            response.raise_for_status()

        logger.info(
            "Historical usage retrieved successfully."
        )

        return response.json()