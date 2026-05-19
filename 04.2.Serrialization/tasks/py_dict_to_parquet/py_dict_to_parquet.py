import pyarrow as pa
import pyarrow.parquet as pq


ValueType = int | list[int] | str | dict[str, str]


def save_rows_to_parquet(rows: list[dict[str, ValueType]], output_filepath: str) -> None:
    """
    Save rows to parquet file.

    :param rows: list of rows containing data.
    :param output_filepath: local filepath for the resulting parquet file.
    :return: None.
    """
    fields_order: list[str] = []
    field_types: dict[str, pa.DataType] = {}
    field_nullable: dict[str, bool] = {}
    all_keys = set()

    def infer_type(value: ValueType) -> pa.DataType:
        if isinstance(value, int):
            return pa.int64()
        if isinstance(value, str):
            return pa.string()
        if isinstance(value, list):
            return pa.list_(pa.int64())
        if isinstance(value, dict):
            return pa.map_(pa.string(), pa.string())
        raise TypeError(f"Unsupported type: {type(value)}")

    for row in rows:
        for key, value in row.items():
            if key not in fields_order:
                fields_order.append(key)
            if value is not None:
                inferred = infer_type(value)
                if key in field_types and field_types[key] != inferred:
                    raise TypeError(f"Field {key} has different types")
                field_types[key] = inferred
        all_keys.update(row.keys())

    for key in fields_order:
        present_in_all = all(key in row for row in rows)
        field_nullable[key] = not present_in_all

    schema_fields = []
    for key in fields_order:
        schema_fields.append(pa.field(key, field_types[key], nullable=field_nullable[key]))

    schema = pa.schema(schema_fields)

    columns: dict[str, list] = {key: [] for key in fields_order}
    for row in rows:
        for key in fields_order:
            columns[key].append(row.get(key))

    arrays = []
    for key in fields_order:
        arrays.append(pa.array(columns[key], type=field_types[key]))

    table = pa.table(dict(zip(fields_order, arrays)), schema=schema)
    pq.write_table(table, output_filepath)
