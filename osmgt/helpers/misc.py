from typing import Dict
from typing import List
from typing import Union
from typing import Any

import time

from functools import wraps


def find_list_dicts_from_key_and_value(
    input_dict: List[Dict], key: str, value: Union[Any]
) -> int:

    for list_idx, values in enumerate(input_dict):
        if values.get(key, None) == value:
            return list_idx
    else:
        raise ValueError(f"{key} == {value} not found")


def retry(Exceptions_to_check, tries: int = 4, delay: int = 3, backoff: int = 2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param Exceptions_to_check: the exception to check. may be a tuple of
        exceptions to check
    :type Exceptions_to_check: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """

    def deco_retry(f):

        @wraps(f)
        def f_retry(*args , **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)

                except Exceptions_to_check as e:
                    msg = f"{str(e)}, Retrying in {mdelay} seconds..."
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry