"""
Holonet

History Poll Service
"""

from __future__ import annotations

from src.api.auth import AuthClient
from src.api.starlink_client import StarlinkClient
from src.api.starlink_client_history import (
    StarlinkHistoryClient
)
from src.config.settings import settings
from src.database.repository import Repository


def run_poll_history() -> None:
    """
    Retrieves historical Starlink Billing information
    and stores it into SQL Server.
    """

    repository = Repository()

    for country, client_id in settings.starlink_clients.items():

        if not client_id:
            continue

        print()
        print("=" * 60)
        print(
            f"Processing Starlink Account: {country}"
        )
        print("=" * 60)

        #
        # Authentication
        #

        auth = AuthClient(client_id)

        token = auth.authenticate()

        #
        # Clients
        #

        client = StarlinkClient(token)

        history_client = StarlinkHistoryClient(
            token
        )

        #
        # Retrieve Account
        #

        print()
        print("Retrieving Account...")

        account = client.get_account()

        print("Account retrieved successfully.")

        #
        # Retrieve Products
        #

        print()
        print("Retrieving Products...")

        products = client.get_products()

        print("Products retrieved successfully.")

        #
        # Retrieve Service Lines
        #

        print()
        print("Retrieving Service Lines...")

        service_lines = client.get_service_lines()

        total = len(
            service_lines["content"]["results"]
        )

        print(
            f"{total} Service Lines found."
        )

        #
        # Update Inventory
        #

        repository.save_service_lines(
            account=account,
            products=products,
            service_lines=service_lines
        )

        #
        # Retrieve Usage History
        #

        print()
        print("Retrieving Usage History...")

        service_line_numbers = [
            service_line["serviceLineNumber"]
            for service_line in service_lines[
                "content"
            ]["results"]
        ]

        history = history_client.get_usage(
            service_line_numbers=service_line_numbers,
            previous_billing_cycles=4
        )

        print(
            "Usage History retrieved successfully."
        )

        #
        # Build SQL Records
        #

        print()
        print(
            "Building Usage History records..."
        )

        records = (
            repository.build_usage_history_records(
                account=account,
                history=history["content"]
            )
        )

        print(
            f"{len(records)} records built."
        )

        #
        # Save Usage History
        #

        print()
        print(
            "Saving Usage History..."
        )

        repository.save_usage_history(
            records
        )

        #
        # Build Reporting Service Usage
        #

        print()
        print(
            "Building Reporting Service Usage..."
        )

        reporting_records = (
            repository.build_reporting_service_usage_records()
        )

        print(
            f"{len(reporting_records)} reporting records built."
        )

        #
        # Save Reporting Service Usage
        #

        print()
        print(
            "Saving Reporting Service Usage..."
        )

        repository.save_reporting_service_usage(
            reporting_records
        )

        print(
            "Reporting Service Usage saved successfully."
        )

        print(
            "Usage History saved successfully."
        )

    print()
    print("=" * 60)
    print("History Poll completed.")
    print("=" * 60)



def main():

    print()
    print("=" * 40)
    print("     HOLONET HISTORY POLL")
    print("=" * 40)

    run_poll_history()

    print()
    print("Done.")


if __name__ == "__main__":

    main()