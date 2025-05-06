"""get_arrow.py module.

Description of the module functionality."""


from .get_bson import get_tabular_bson_head
from .meta_config import (
    __META_FIELDS__,
    __META_INFO__,
    __META_TABLES__,
    __TABULAR_PERIODS__,
    _init_metainfos,
)


def _get_tabular_feather_single_ori(
    codes: list,
    table: str,
    int_period: int,
    start_timetag: int,
    end_timetag: int,
    count: int = -1,
    **kwargs,
):
"""Args::
    codes: 
    table: 
    int_period: 
    start_timetag: 
    end_timetag: 
    count: (Default value = -1)"""
    count: (Default value = -1)"""
    import os

    from pyarrow import feather as fe

    from .. import xtdata

    CONSTFIELD_TIME = "_time"
    CONSTFIELD_CODE = "_stock"

    file_path = os.path.join(xtdata.get_data_dir(), "EP", f"{table}_Xdat2", "data.fe")
    if not os.path.exists(file_path):
        return

    fe_table = fe.read_table(file_path)

    schema = fe_table.schema
    fe_fields = [f.name for f in schema]

    def _old_arrow_filter():
""""""
""""""
""""""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    codes: 
    fields: 
    period: 
    start_time: 
    end_time: 
    count: (Default value = -1)"""
    count: (Default value = -1)"""
    import pandas as pd

    time_format = None
    if period in ("1m", "5m", "15m", "30m", "60m", "1h"):
        time_format = "%Y-%m-%d %H:%M:%S"
    elif period in ("1d", "1w", "1mon", "1q", "1hy", "1y"):
        time_format = "%Y-%m-%d"
    elif period == "":
        time_format = "%Y-%m-%d %H:%M:%S.%f"

    if not time_format:
        raise Exception("Unsupported period")

    int_period = __TABULAR_PERIODS__[period]

    if not isinstance(count, int) or count == 0:
        count = -1

    table_fields = _parse_fields(fields)

    def datetime_to_timetag(timelabel, format=""):
"""timelabel: str '20221231' '20221231235959'
format: str '%Y%m%d' '%Y%m%d%H%M%S'

Args::
    timelabel: 
    format: (Default value = "")"""
    format: (Default value = "")"""
        import datetime as dt

        if not format:
            format = "%Y%m%d" if len(timelabel) == 8 else "%Y%m%d%H%M%S"
        try:
            return dt.datetime.strptime(timelabel, format).timestamp() * 1000
        except BaseException:
            return 0

    start_timetag = datetime_to_timetag(start_time)
    end_timetag = datetime_to_timetag(end_time)

    dfs = []
    ordered_fields = []
    for table, show_fields, fe_fields in table_fields:
        fe_table, fe_table_fields = _get_tabular_feather_single_ori(
            codes, table, int_period, start_timetag, end_timetag, count
        )
        if not fe_table:
            continue

        ifields = list(set(fe_table_fields) & set(fe_fields))
        if not ifields:
            continue

        fe_table = fe_table.select(ifields)
        fe_df = fe_table.to_pandas()
        # 补充请求的字段
        default_null_columns = [f for f in fe_fields if f not in fe_table_fields]
        for c in default_null_columns:
            fe_df.loc[:, c] = pd.NA

        rename_fields = {}

        for i in range(min(len(show_fields), len(fe_fields))):
            show_field = f"{table}.{show_fields[i]}"
            rename_fields[fe_fields[i]] = show_field
            ordered_fields.append(show_field)

        fe_df.rename(columns=rename_fields, inplace=True)
        dfs.append(fe_df)

    if not dfs:
        return pd.DataFrame()

    result = pd.concat(dfs, ignore_index=True)
    return result[ordered_fields]


def get_tabular_fe_bson(
    codes: list,
    fields: list,
    period: str,
    start_time: str,
    end_time: str,
    count: int = -1,
    **kwargs,
):
"""Args::
    codes: 
    fields: 
    period: 
    start_time: 
    end_time: 
    count: (Default value = -1)"""
    count: (Default value = -1)"""
    from .. import xtbson

    time_format = None
    if period in ("1m", "5m", "15m", "30m", "60m", "1h"):
        time_format = "%Y-%m-%d %H:%M:%S"
    elif period in ("1d", "1w", "1mon", "1q", "1hy", "1y"):
        time_format = "%Y-%m-%d"
    elif period == "":
        time_format = "%Y-%m-%d %H:%M:%S.%f"

    if not time_format:
        raise Exception("Unsupported period")

    int_period = __TABULAR_PERIODS__[period]

    if not isinstance(count, int) or count == 0:
        count = -1

    table_fields = _parse_keys(fields)

    def datetime_to_timetag(timelabel, format=""):
"""timelabel: str '20221231' '20221231235959'
format: str '%Y%m%d' '%Y%m%d%H%M%S'

Args::
    timelabel: 
    format: (Default value = "")"""
    format: (Default value = "")"""
        import datetime as dt

        if not format:
            format = "%Y%m%d" if len(timelabel) == 8 else "%Y%m%d%H%M%S"
        try:
            return dt.datetime.strptime(timelabel, format).timestamp() * 1000
        except BaseException:
            return 0

    start_timetag = datetime_to_timetag(start_time)
    end_timetag = datetime_to_timetag(end_time)

    def _get_convert():
""""""
"""Args::
    table:"""
"""Args::
    table:"""
    table:"""
            return table.to_pylist()

        paver = version.LooseVersion(pa.__version__)
        if paver < version.LooseVersion("7.0.0"):
            return _old_arrow_convert
        else:
            return _new_arrow_convert

    convert = _get_convert()
    ret_bsons = []
    for table, show_fields, fe_fields in table_fields:
        table_head = get_tabular_bson_head(fields)
        ret_bsons.append(xtbson.encode(table_head))

        fe_table, fe_table_fields = _get_tabular_feather_single_ori(
            codes, table, int_period, start_timetag, end_timetag, count
        )

        ifields = list()
        new_columns = list()
        for i in range(len(fe_fields)):
            if fe_fields[i] in fe_table_fields:
                ifields.append(fe_fields[i])
                new_columns.append(show_fields[i])

        if not ifields:
            continue

        fe_table = fe_table.select(ifields)
        fe_table = fe_table.rename_columns(new_columns)  # key_column

        fe_datas = convert(fe_table)
        for data in fe_datas:
            ret_bsons.append(xtbson.encode(data))

    return ret_bsons
