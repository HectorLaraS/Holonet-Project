"""
Holonet

Scheduler
"""

from datetime import datetime
from time import sleep

from src.config.settings import settings
from src.main import run_poll
from src.main import run_report


def main():

    print()
    print("=" * 50)
    print("         HOLONET SCHEDULER")
    print("=" * 50)
    print()

    last_poll = datetime.min
    last_report = datetime.min

    while True:

        now = datetime.now()

        #
        # Poll Scheduler
        #

        poll_elapsed = (
            now - last_poll
        ).total_seconds()

        if poll_elapsed >= settings.POLL_INTERVAL_SECONDS:

            print()

            print(
                f"[{now:%Y-%m-%d %H:%M:%S}] "
                "Starting Poll..."
            )

            try:

                run_poll()

                last_poll = now

                print()

                print("Poll completed successfully.")

            except Exception as error:

                print()

                print(
                    f"Poll failed: {error}"
                )

        #
        # Report Scheduler
        #

        report_elapsed = (
            now - last_report
        ).total_seconds()

        if report_elapsed >= settings.REPORT_INTERVAL_SECONDS:

            print()

            print(
                f"[{now:%Y-%m-%d %H:%M:%S}] "
                "Generating Report..."
            )

            try:

                run_report()

                last_report = now

                print()

                print("Report generated successfully.")

            except Exception as error:

                print()

                print(
                    f"Report failed: {error}"
                )

        sleep(1)


if __name__ == "__main__":
    main()