"""
Holonet

SQL Loader
"""

from __future__ import annotations

from pathlib import Path


class SQLLoader:
    """
    Loads SQL statements stored in the project's sql directory.
    """

    @staticmethod
    def load(filename: str) -> str:
        """
        Loads a SQL file and returns its contents.

        Parameters
        ----------
        filename : str
            SQL file name.

        Returns
        -------
        str
            SQL statement.
        """

        sql_path = (
            Path(__file__).resolve().parent.parent
            / "sql"
            / filename
        )

        with open(
            sql_path,
            mode="r",
            encoding="utf-8"
        ) as sql_file:

            return sql_file.read()