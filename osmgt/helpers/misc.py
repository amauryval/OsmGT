def find_index(dicts, key, value):

    for idx, values in enumerate(dicts):
        if values.get(key, None) == value:
            return idx
    else:
        raise ValueError('Not found')