from module_settings import Settings, Color
from module_db_sqlite import db_log, db_error
from datetime import datetime
from pathlib import Path
import requests
import inspect
import pickle
import json


def requests_get(url: str, timeout: tuple = (10, 30)) -> any:
    """ Getting a server response to a request
        example: timeout=(10, 30) --> connect=10, read=30 """

    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                "Chrome/92.0.4515.159 Safari/537.36"
    headers = {'Content-Type': 'text/html', 'user-agent': useragent}
    try:
        res = requests.get(url, headers=headers, timeout=timeout)
        if res and res.status_code < 400:
            return res, ('info', '', f"{res.status_code} {url}")
        else:
            return None, ('error', '', f"{res.status_code} {url}")
    except Exception as err:
        if "res" not in locals():
            return None, ('critical', '', f"Critical error ! No internet connection !")
        else:
            return None, ('critical', '', f"No internet connection ! [{url}] \n{err}")


def is_file_exists(file_name: str = '', print_enable: bool = True) -> bool:
    """ Checking if a file exists """
    try:
        _path = Path(Settings.db_path / file_name)
        _ = True if file_name and _path.exists() else False
        if print_enable:
            db_log(('process', '', f'{str(_path)} is exists') if _ else
                   ('warning', '', f'{str(_path)} not found'))
        return _
    except Exception as err:
        db_error(err)
        return False


def is_module_started(module_doc: str = '') -> None:
    """ Printing information about the active module """
    db_log(('process', '', f'Start module [{inspect.stack()[1][3]}] - [{module_doc.strip()}]'))


def is_datetime(datetime_value=datetime.now(), datetime_mode: str = "datetime"):
    """  """
    match datetime_mode:
        case 'date':
            return f"{datetime_value}"[:10]    # '2021-07-28'
        case 'time':
            return f"{datetime_value}"[11:-7]  # '21:44:40'
        case 'datetime':
            return f"{datetime_value}"[:-7]    # '2021-07-28 21:44:40'
    return f"{datetime_value}"                 # '2021-07-28 21:35:03.052364'


def text_findall(str_in: str = '', str_start: str = '', str_end: str = '',
                 str_include: str = '', str_exclude: str = '', str_duplicate: str = 'no') -> list:
    """ Create a list of strings from [str_in] what should be between strings [str_start ... str_end]
        [str_include='aaa']  - selected lines must include the text 'aaa'
        [str_exclude='bbb']  - selected lines are not guilty include text 'bbb'
        [str_duplicate='no'] - turn on duplicates from the list """
    str_out_list = []
    try:
        if all([isinstance(_, str) for _ in locals().keys()]) and all([str_in, str_start, str_end]):
            pos, pos_start, pos_end = 0, 0, 0
            while (pos_start := str_in.find(str_start, pos)) != -1 and pos_end != -1:
                if (pos_end := str_in.find(str_end, pos_start + len(str_start))) != -1:
                    str_out = str_in[pos_start + len(str_start):pos_end]
                    if not ((str_include and str_include not in str_out) or
                            (str_exclude and str_exclude in str_out) or
                            (str_duplicate and str_out in str_out_list)):
                        str_out_list.append(str_out)
                    pos = pos_end + len(str_end)
        return str_out_list
    except Exception as err:
        db_error(err)
        return []


def list_select_duplicates(list_in: any) -> list:
    """ Select duplicates from the list """
    try:
        _set = set()
        return [_ for _ in list_in if _ in _set or (_set.add(_) or False)]
    except Exception as err:
        db_error(err)
        return []


# def print_log(line: str | tuple | list, line_level: str = 'process', log_enable: bool = True) -> None:
#     """ Displays the strings on the screen """
#     try:
#         match type(line):
#             case 'str': db_log(lines=(line_level, '', line), log_enable=log_enable)
#             case 'tuple' | 'list': db_log(lines=line, log_enable=log_enable)
#             case _: raise Exception(f"Wrong type of variable [line] [{type(line)}]")
#     except Exception as err:
#         db_error(err)
#     return None
# 
# 
# def db_error(err: Exception) -> None:
#     """ Printing information about the module errors """
#     # db_log(lines=('error', '', f"Error in module [{inspect.stack()[1][3]}]. [{err}]"))
#     print_log(('error', '', f"Error in module [{inspect.stack()[1][3]}]. [{err}]"))
#     return None


# ********************************************************************
def json_dump(file_name: str, file_data: any, encoding: str = "utf-8") -> bool:
    """ Saving a Python Object in a JSON file """
    try:
        print(f'[{file_name}] {Color.white}{json_dump.__doc__.strip()} ...{Color.end}', end="")
        with open(file_name, 'w', encoding=encoding) as f:
            json.dump(file_data, f)
        print(f"{Color.green} Completed.{Color.end}")
        return True
    except Exception as err:
        db_error(err)
        return False


def json_load(file_name: str) -> any:
    """ Get Python object from JSON file """
    try:
        print(f'[{file_name}] {Color.white}{json_load.__doc__.strip()} ...{Color.end}', end="")
        with open(file_name, 'r') as f:
            file_data = json.load(f)
        print(f"{Color.green} Completed.{Color.end}")
        return file_data
    except Exception as err:
        db_error(err)
        return False


def pickle_dump(file_name: str, file_data: any) -> bool:
    """ Saving a Python Object in a Pickle file """
    try:
        print(f'[{file_name}] {Color.white}{pickle_dump.__doc__.strip()} ...{Color.end}', end="")
        with open(file_name, 'wb') as f:
            pickle.dump(file_data, f)
        print(f"{Color.green} Completed.{Color.end}")
        return True
    except Exception as err:
        db_error(err)
        return False


def pickle_load(file_name: str) -> any:
    """ Get Python object from Pickle file """
    try:
        print(f'[{file_name}] {Color.white}{pickle_load.__doc__.strip()} ...{Color.end}', end="")
        with open(file_name, 'rb') as f:
            file_data = pickle.load(f)
        print(f"{Color.green} Completed.{Color.end}")
        return file_data
    except Exception as err:
        db_error(err)
        return False


# *****************************************************************
# class Color:
#     end = '\033[0m'
#     black = '\033[30m'
#     red = '\033[31m'     # "\x1b[91m"
#     green = '\033[32m'   # "\x1b[92m"
#     yellow = '\033[33m'  # "\x1b[93m"
#     blue = '\033[34m'
#     purple = '\033[35m'
#     cyan = '\033[36m'
#     white = '\033[37m'
#     grey = '\033[90m'
#
#
# color_log = dict(
#     debug=Color.grey,
#     info=Color.white,
#     process=Color.green,
#     critical=Color.red,
#     error=Color.red,
#     warning=Color.yellow)
