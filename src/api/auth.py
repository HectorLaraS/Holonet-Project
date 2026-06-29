"""
Holonet

Starlink OAuth Client
"""

from __future__ import annotations

import requests

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AuthClient:
    """
    Handles authentication against the Starlink OAuth API.
    """

    def __init__(
        self,
        client_id: str
    ):

        self.auth_url = settings.auth_url

        self.client_id = client_id

        self.client_secret = settings.client_secret

        self.timeout = settings.timeout

    def authenticate(self) -> str:
        """
        Requests an OAuth access token.

        Returns
        -------
        str
            OAuth access token.
        """

        logger.info(
            f"Requesting Starlink OAuth token "
            f"for client '{self.client_id}'..."
        )

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(
            self.auth_url,
            headers=headers,
            data=payload,
            timeout=self.timeout
        )

        response.raise_for_status()

        token = response.json()["access_token"]

        logger.info(
            f"OAuth token obtained successfully "
            f"for client '{self.client_id}'."
        )

        return token