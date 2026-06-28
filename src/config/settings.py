"""
Holonet

Application Settings
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Application configuration.
    """

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------

    db_server = os.getenv("DB_SERVER")

    db_database = os.getenv("DB_DATABASE")

    db_username = os.getenv("DB_USERNAME")

    db_password = os.getenv("DB_PASSWORD")

    driver = os.getenv(
        "DB_DRIVER",
        "ODBC Driver 18 for SQL Server"
    )

    # -------------------------------------------------------------------------
    # Starlink
    # -------------------------------------------------------------------------

    auth_url = os.getenv("STARLINK_AUTH_URL")

    api_base_url = os.getenv("STARLINK_API_BASE_URL")

    client_id = os.getenv("STARLINK_CLIENT_ID")

    client_secret = os.getenv("STARLINK_CLIENT_SECRET")

    timeout = int(
        os.getenv("API_TIMEOUT", "30")
    )

    # -------------------------------------------------------------------------
    # Reports
    # -------------------------------------------------------------------------

    export_path = os.getenv(
        "EXPORT_PATH",
        "./exports"
    )

    POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS","300"))

    REPORT_INTERVAL_SECONDS = int(os.getenv("REPORT_INTERVAL_SECONDS","43200"))

    SERVICE_RESTART_DELAY_SECONDS = int(os.getenv("SERVICE_RESTART_DELAY_SECONDS","5"))


settings = Settings()