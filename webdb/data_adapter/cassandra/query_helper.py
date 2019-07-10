import logging
_logger = logging.getLogger(__name__)


async def inject_column_name(data_rows: list, param_names: (list, tuple)) -> list:
    """
    Inject columns' name into data
    :param data_rows: list of data fetched from DB
    :param param_names: <list, tuple> parameters names
    :return: <list of dict> Data fetched from DB
    """
    result = []
    for row in data_rows:
        data_result = {}
        for i, name in enumerate(param_names):
            if i >= len(row):
                # print("XXXX: #{}  {} <{}>".format(i, row, param_names))
                break
            data_result[name] = row[i]
        result.append(data_result)
    return result

