from src.api.auth import AuthClient
from src.api.starlink_client import StarlinkClient
from src.database.repository import Repository
from src.excel.exporter import ExcelExporter


def main():

    auth = AuthClient()

    token = auth.authenticate()

    client = StarlinkClient(token)

    repository = Repository()

    products = client.get_products()
    repository.save_products(products)

    usage = client.get_usage()
    repository.save_usage(usage)

    exporter = ExcelExporter()

    output_file = exporter.export_report()

    print()

    print("Excel generated successfully.")

    print(output_file)

    print()

    print("Process completed successfully.")


if __name__ == "__main__":
    main()