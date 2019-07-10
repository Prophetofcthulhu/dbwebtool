
def repack_as_dict(rows: list, names: list) -> list:
    result = []
    for items in rows:
        if isinstance(items, dict):
            result.append(items)
            # index = items.get("table_name")
            # if index:
            #     result.append({index: items})
        else:
            item = {}
            for i, value in enumerate(items):
                item[names[i]] = value
            result.append(item)
    return result
