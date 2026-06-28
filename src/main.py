"""
Holonet

Main Entry Point
"""

from src.api.auth import AuthClient
from src.api.starlink_client import StarlinkClient
from src.database.repository import Repository
from src.excel.exporter import ExcelExporter


def run_poll() -> None:
    """
    Retrieves information from Starlink
    and stores it in SQL Server.
    """

    auth = AuthClient()

    token = auth.authenticate()

    client = StarlinkClient(token)

    repository = Repository()

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