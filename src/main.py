"""
Holonet

Main Entry Point
"""

from src.api.auth import AuthClient
from src.api.starlink_client import StarlinkClient
from src.config.settings import settings
from src.database.repository import Repository
from src.excel.exporter import ExcelExporter


def run_poll() -> None:
    """
    Retrieves information from all configured
    Starlink accounts and stores it in SQL Server.
    """

    repository = Repository()

    for country, client_id in settings.starlink_clients.items():

        if not client_id:
            continue

        print()
        print("=" * 50)
        print(f"Processing Starlink Account: {country}")
        print("=" * 50)

        auth = AuthClient(client_id)

        token = auth.authenticate()

        client = StarlinkClient(token)

        print()
        print("Retrieving Products...")

        products = client.get_products()

        repository.save_products(products)

        print("Products updated successfully.")

        print()
        print("Retrieving Usage...")

        usage = client.get_usage()

        repository.save_usage(usage)

        print("Usage updated successfully.")

        print()
        print("Retrieving Service Line Details...")

        for service_line in usage["content"]["results"]:

            details = client.get_service_line(
                service_line["serviceLineNumber"]
            )

            repository.save_service_line_details(
                details
            )

        print("Service Line Details updated successfully.")


def run_report() -> None:
    """
    Generates the Excel report
    using the latest SQL Server data.
    """

    exporter = ExcelExporter()

    output_file = exporter.export_report()

    print()

    print("Excel generated successfully.")

    print(output_file)


def main():

    while True:

        print()
        print("=" * 40)
        print("             HOLONET")
        print("=" * 40)
        print()
        print("1. Poll Starlink")
        print("2. Generate Excel")
        print("3. Poll + Generate Excel")
        print("0. Exit")
        print()

        option = input("Option: ").strip()

        print()

        if option == "1":

            run_poll()

        elif option == "2":

            run_report()

        elif option == "3":

            run_poll()

            print()

            run_report()

        elif option == "0":

            print("Bye.")

            break

        else:

            print("Invalid option.")


if __name__ == "__main__":
    main()