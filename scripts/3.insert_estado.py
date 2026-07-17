import csv
import sys
from pathlib import Path

import polars as pl
import mysql.connector
from mysql.connector import Error

ESTADO_DIR = Path(__file__).resolve().parent.parent / "docs" / "entregas" / "estado"
files = sorted(ESTADO_DIR.glob("*.csv"))

ATRIBUTOS = [
    "station_id",
    "num_bikes_available",
    "num_bikes_available_types.mechanical",
    "num_bikes_available_types.ebike",
    "num_docks_available",
    "last_reported",
]

COLUMNAS_FINALES = [
    "station_id",
    "num_bikes_available",
    "num_bikes_available_mechanical",
    "num_bikes_available_ebike",
    "num_docks_available",
    "datetime",
]

INSERT_ESTADO = """
    INSERT IGNORE INTO estado (
        station_id,
        num_bikes_available,
        num_bikes_available_mechanical,
        num_bikes_available_ebike,
        num_docks_available,
        datetime
    ) VALUES (%s, %s, %s, %s, %s, %s)
"""


def _header_columns(file):
    with open(file, "r", encoding="utf-8-sig", errors="replace") as f:
        line = f.readline()
    return [col.strip().strip('"') for col in line.split(",") if col.strip()]


def _detect_encoding(file):
    for encoding in ("utf8", "windows-1252", "utf8-lossy"):
        try:
            pl.read_csv(file, n_rows=1, encoding=encoding, try_parse_dates=False)
            return encoding
        except (UnicodeDecodeError, pl.exceptions.ComputeError):
            continue
    raise RuntimeError(f"No se pudo detectar la codificación de {file}")


def _read_estado_batched(file):
    present_cols = [col for col in _header_columns(file) if col in ATRIBUTOS]
    overrides = {col: pl.Float64 for col in present_cols}
    encoding = _detect_encoding(file)
    return pl.read_csv_batched(
        file,
        columns=present_cols,
        schema_overrides=overrides,
        encoding=encoding,
        try_parse_dates=False,
        null_values=["NA", "N/A", "NULL", "null", "None", "NaN", "nan"],
        batch_size=200_000,
    )


def _normalizar_df(df):
    df = df.filter(
        pl.col("station_id").is_not_null() & pl.col("last_reported").is_not_null()
    )
    df = df.with_columns(pl.col("station_id").cast(pl.Int64, strict=False))

    df = df.rename(
        {
            "num_bikes_available_types.mechanical": "num_bikes_available_mechanical",
            "num_bikes_available_types.ebike": "num_bikes_available_ebike",
        },
        strict=False,
    )

    df = df.with_columns(
        pl.from_epoch(
            pl.col("last_reported").cast(pl.Int64, strict=False),
            time_unit="s",
        ).alias("datetime")
    ).drop("last_reported")

    expected = {
        "station_id": pl.Int64,
        "num_bikes_available": pl.Int64,
        "num_bikes_available_mechanical": pl.Int64,
        "num_bikes_available_ebike": pl.Int64,
        "num_docks_available": pl.Int64,
        "datetime": pl.Datetime("us"),
    }

    for col, dtype in expected.items():
        if col not in df.columns:
            df = df.with_columns(pl.lit(None).cast(dtype).alias(col))
        else:
            df = df.with_columns(pl.col(col).cast(dtype, strict=False))

    df = df.unique(
        subset=["station_id", "datetime"], keep="last", maintain_order=True
    )
    return df.select(list(expected.keys()))


def insert_estado():
    connection = None
    try:
        connection = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            database="Bicing",
        )
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM informacion")
        if cursor.fetchone()[0] == 0:
            raise RuntimeError(
                "La tabla informacion está vacía; carga sus estaciones antes de insertar estado."
            )

        total = 0
        for file in reversed(files):
            reader = _read_estado_batched(file)
            archivo_total = 0
            while True:
                batches = reader.next_batches(5)
                if not batches:
                    break
                for df in batches:
                    df = _normalizar_df(df)
                    for start in range(0, df.height, 5_000):
                        sub = df.slice(start, 5_000)
                        rows = [tuple(row) for row in sub.iter_rows(named=False)]
                        if rows:
                            cursor.executemany(INSERT_ESTADO, rows)
                            connection.commit()
                    archivo_total += df.height
            total += archivo_total
            print(f"{file.name}: {archivo_total} registros insertados/actualizados")

        cursor.close()
        print(f"Total: {total} registros insertados/actualizados en estado.")
    except (Error, RuntimeError) as error:
        print(f"No se pudieron insertar los registros: {error}", file=sys.stderr)
        sys.exit(1)
    finally:
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    insert_estado()
