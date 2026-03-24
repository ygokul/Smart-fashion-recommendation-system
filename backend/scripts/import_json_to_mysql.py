import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List

import mysql.connector


TABLE_ORDER = [
    "users",
    "user_profiles",
    "user_sessions",
    "chat_messages",
    "images",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import seed JSON into MySQL for Smart Fashion.")
    parser.add_argument("json_file", help="Path to the seed JSON file")
    parser.add_argument("--truncate", action="store_true", help="Clear known tables before importing")
    return parser.parse_args()


def load_payload(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        raise ValueError("Top-level JSON must be an object keyed by table name, not a list")
    return data


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "smart_fashion"),
    )


def normalize_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return value


def truncate_tables(cursor, tables: Iterable[str]) -> None:
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    try:
        for table in reversed(list(tables)):
            cursor.execute(f"TRUNCATE TABLE {table}")
    finally:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")


def upsert_rows(cursor, table: str, rows: List[Dict[str, Any]]) -> int:
    if not rows:
        return 0

    columns = list(rows[0].keys())
    placeholders = ", ".join(["%s"] * len(columns))
    column_list = ", ".join(columns)
    update_list = ", ".join([f"{column} = VALUES({column})" for column in columns if column != "id"])
    sql = f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"
    if update_list:
        sql += f" ON DUPLICATE KEY UPDATE {update_list}"

    values = [tuple(normalize_value(row.get(column)) for column in columns) for row in rows]
    cursor.executemany(sql, values)
    return len(values)


def main() -> None:
    args = parse_args()
    json_path = Path(args.json_file).resolve()
    payload = load_payload(json_path)

    connection = get_connection()
    cursor = connection.cursor()
    try:
        present_tables = [table for table in TABLE_ORDER if table in payload]
        if args.truncate:
            truncate_tables(cursor, present_tables)

        imported = {}
        for table in TABLE_ORDER:
            rows = payload.get(table, [])
            imported[table] = upsert_rows(cursor, table, rows)

        connection.commit()
    finally:
        cursor.close()
        connection.close()

    for table, count in imported.items():
        print(f"{table}: imported {count} row(s)")


if __name__ == "__main__":
    main()