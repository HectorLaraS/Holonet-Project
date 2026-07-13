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

    client_secret = os.getenv("STARLINK_CLIENT_SECRET")

    timeout = int(
        os.getenv("API_TIMEOUT", "30")
    )

    starlink_clients = {
        "US": os.getenv("STARLINK_CLIENT_ID_US"),
        "CA": os.getenv("STARLINK_CLIENT_ID_CA"),
        "MX": os.getenv("STARLINK_CLIENT_ID_MX")
    }

    # -------------------------------------------------------------------------
    # Reports
    # -------------------------------------------------------------------------

    export_path = os.getenv(
        "EXPORT_PATH",
        "./exports"
    )

    POLL_INTERVAL_SECONDS = int(
        os.getenv(
            "POLL_INTERVAL_SECONDS",
            "300"
        )
    )

    REPORT_INTERVAL_SECONDS = int(
        os.getenv(
            "REPORT_INTERVAL_SECONDS",
            "43200"
        )
    )

    # -------------------------------------------------------------------------
    # History
    # -------------------------------------------------------------------------

    REPORT_HISTORY_INTERVAL_SECONDS = int(
        os.getenv(
            "REPORT_HISTORY_INTERVAL_SECONDS",
            "86400"
        )
    )

    BILLING_CYCLES_HISTORY = int(
        os.getenv(
            "BILLING_CYCLES_HISTORY",
            "4"
        )
    )

    SERVICE_RESTART_DELAY_SECONDS = int(
        os.getenv(
            "SERVICE_RESTART_DELAY_SECONDS",
            "5"
        )
    )

    SERVICE_RESTART_DELAY_SECONDS = int(
        os.getenv(
            "SERVICE_RESTART_DELAY_SECONDS",
            "5"
        )
    )

    #------------------------------------------------------------------------------
    # ANALYTICS
    #------------------------------------------------------------------------------

    ANALYTICS_HIGH_CONFIDENCE_THRESHOLD = float(
        os.getenv(
            "ANALYTICS_HIGH_CONFIDENCE_THRESHOLD",
            "0.10"
        )
    )

    ANALYTICS_MEDIUM_CONFIDENCE_THRESHOLD = float(
        os.getenv(
            "ANALYTICS_MEDIUM_CONFIDENCE_THRESHOLD",
            "0.25"
        )
    )

    ANALYTICS_OPERATIONAL_REVIEW_MIN_TOPUPS = int(
        os.getenv(
            "ANALYTICS_OPERATIONAL_REVIEW_MIN_TOPUPS",
            "3"
        )
    )

    ANALYTICS_OPERATIONAL_REVIEW_HIGH_TOPUPS = int(
        os.getenv(
            "ANALYTICS_OPERATIONAL_REVIEW_HIGH_TOPUPS",
            "6"
        )
    )

    ANALYTICS_RECURRING_BLOCK_SIZE_GB = int(
        os.getenv(
            "ANALYTICS_RECURRING_BLOCK_SIZE_GB",
            "500"
        )
    )

    ANALYTICS_MONTHS_PER_YEAR = int(
        os.getenv(
            "ANALYTICS_MONTHS_PER_YEAR",
            "12"
        )
    )

    ANALYTICS_MINIMUM_BILLING_CYCLES = int(
        os.getenv(
            "ANALYTICS_MINIMUM_BILLING_CYCLES",
            "2"
        )
    )

    #------------------------------------------------------------------------------
    # STARLINK PRICING
    #------------------------------------------------------------------------------

    STARLINK_US_50GB_PRICE = float(
        os.getenv(
            "STARLINK_US_50GB_PRICE",
            "25.00"
        )
    )

    STARLINK_US_500GB_PRICE = float(
        os.getenv(
            "STARLINK_US_500GB_PRICE",
            "125.00"
        )
    )

    STARLINK_CA_50GB_PRICE = float(
        os.getenv(
            "STARLINK_CA_50GB_PRICE",
            "32.50"
        )
    )

    STARLINK_CA_500GB_PRICE = float(
        os.getenv(
            "STARLINK_CA_500GB_PRICE",
            "162.50"
        )
    )

    STARLINK_MX_50GB_PRICE = float(
        os.getenv(
            "STARLINK_MX_50GB_PRICE",
            "500.00"
        )
    )

    STARLINK_MX_500GB_PRICE = float(
        os.getenv(
            "STARLINK_MX_500GB_PRICE",
            "2500.00"
        )
    )


settings = Settings()