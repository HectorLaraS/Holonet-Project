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

from src.api.auth import AuthClient
from src.api.starlink_client import StarlinkClient
from src.api.starlink_client_history import StarlinkHistoryClient
from src.config.settings import settings
from src.excel.exporter_history import HistoryExporter


def run_history() -> None:
    """
    Retrieves historical Starlink usage information
    and generates the History Excel report.
    """

    history_usage = {
        "content": {
            "results": []
        }
    }

    for country, client_id in settings.starlink_clients.items():

        if not client_id:
            continue

        print()
        print("=" * 60)
        print(f"Processing Starlink Account: {country}")
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

        history_client = StarlinkHistoryClient(token)

        #
        # Retrieve Service Lines
        #

        print()
        print("Retrieving Service Lines...")

        usage = client.get_usage()

        total = len(
            usage["content"]["results"]
        )

        print(
            f"{total} Service Lines found."
        )

        print()
        print("Retrieving Historical Usage...")

        for index, service_line in enumerate(
            usage["content"]["results"],
            start=1
        ):

            service_line_number = (
                service_line["serviceLineNumber"]
            )

            print(
                f"[{index}/{total}] "
                f"{service_line_number}"
            )

            #
            # Retrieve Service Line Details
            #

            details = client.get_service_line(
                service_line_number
            )

            #
            # Retrieve Historical Usage
            #

            history = history_client.get_usage(
                service_line_numbers=[
                    service_line_number
                ],
                previous_billing_cycles=3
            )

            #
            # Enrich History Result
            #

            if history["content"]["results"]:

                history_result = (
                    history["content"]["results"][0]
                )

                details_content = details.get(
                    "content",
                    {}
                )

                history_result["nickname"] = (
                    details_content.get(
                        "nickname",
                        ""
                    )
                )

                history_result["productReferenceId"] = (
                    details_content.get(
                        "productReferenceId",
                        ""
                    )
                )

                #
                # Temporary validation
                #

                print(
                    f"Nickname: "
                    f"{history_result['nickname']}"
                )

                history_usage["content"]["results"].append(
                    history_result
                )

        print()
        print(
            "Historical Usage retrieved successfully."
        )

    #
    # Generate Excel
    #

    print()
    print("=" * 60)
    print("Generating History Excel...")
    print("=" * 60)

    exporter = HistoryExporter(
        history_usage
    )

    output_file = exporter.export_report()

    print()
    print(
        "History Excel generated successfully."
    )

    print(output_file)


def main():

    print()
    print("=" * 40)
    print("      HOLOLINK HISTORY")
    print("=" * 40)

    run_history()

    print()

    print("Done.")


if __name__ == "__main__":
    main()