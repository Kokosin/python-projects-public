import sqlite3
import inspect
import pickle
import sys

from module_settings import db_structure, Settings, color_log, Color
# from module_functions import db_error, print_log


def db_start() -> bool:
    """ Creating and opening sqlite database tables """
    try:
        if not db_tables():
            cur.executescript(db_structure)
            db_log(('process', f'{Settings.db_file}', 'Creating sqlite database.'))
        cur.executescript("PRAGMA foreign_keys=on;")                                # включить поддержку внешних ключей
        con.commit()
        db_log(('process', f'{Settings.db_file}', 'Connecting sqlite database.'))
        return True
    except Exception as err:
        db_error(err)
        sys.exit()


def db_close(print_enable=True) -> bool:
    """ Closing the connection to the sqlite database """
    try:
        if con:
            con.close()
            if print_enable:
                db_log(('process', f'{Settings.db_file}', 'Database Sqlite is closed.'))
        return True
    except Exception as err:
        db_error(err)
        return False


def db_check_con() -> bool:
    """ Checking Sqlite DB connection """
    try:
        con.cursor()
        db_log(('process', f'{Settings.db_file}', 'Connecting sqlite database.'))
        return True
    except Exception as err:
        db_log(('warning', f'{Settings.db_file}', f'Not connecting sqlite database. [{err}]'))
        return False


def db_tables() -> list:
    """ Getting a list of database tables """
    try:
        tables = cur.execute('SELECT name from sqlite_master where type= "table"').fetchall()
        return [] if not tables else [x[0] for x in tables]
    except Exception as err:
        db_error(err)
        return []


def db_table_fields(table_name: str = "") -> list:
    """ Getting a list of fields in a database table """
    try:
        return [x[1] for x in cur.execute(f"pragma table_info({table_name})")]
    except Exception as err:
        db_error(err)
        return []


def db_table_delete(table_name: str = "") -> bool:
    """ Delete table from database """
    try:
        cur.execute(f"drop table if exist {table_name}")
        return True
    except Exception as err:
        db_error(err)
        return False


def db_fields(table_count_fields: int) -> str:
    """ Creating a value string (?,?,?) for a table """
    return f"{('?, ' * table_count_fields)[:-2]}"       # (', ?' * 7)[2:]


def db_select(table_query) -> any:
    """ Selecting records from a database table """
    try:
        cur.execute(table_query)
        return cur.fetchall()
    except Exception as err:
        db_error(err)
        return None


def db_insert(table_query, table_data, commit=True, mode="", print_enable=True) -> any:
    """ Updates rows in a table (mode --> '' or 'executemany' """
    # table_data --> executemany - список кортежів, execute - список
    try:
        cur.execute(table_query, table_data) if not mode else cur.executemany(table_query, table_data)
        if commit:
            con.commit()
        return cur.rowcount
    except Exception as err:
        if print_enable:
            db_error(err)
        return None


def db_insert_many(mode="executemany", table_name="", table_data=None) -> any:
    """ We insert a list of records into the table with a check of the result """
    try:
        if table_name and table_data:
            if mode == "executemany":                                                   # insert - весь список
                _ = db_insert(table_query=f"INSERT INTO {table_name} VALUES ({db_fields(len(table_data[0])) })",
                              table_data=table_data, commit=True, mode='executemany')
                db_log((f"{'' if _ == len(table_data) else 'warning'}", table_name,
                       f"Total rows: {len(table_data):>5} Insert : {_}"))
            else:                                                                      # insert - список - по елементу
                _ = list()                                                             # список [1,1,None,1]
                for _rows, _table_data in enumerate(table_data):
                    _.append(db_insert(table_query=f"INSERT INTO {table_name} VALUES ({db_fields(len(_table_data))})",
                                       table_data=_table_data, commit=False, print_enable=False))
                db_log((f"{'' if all(_) else 'warning'}", table_name,
                       f"Total rows: {len(table_data):>5} Insert : {_.count(1)}"))    # {_} список [1,1,None,1]
                # con.commit()                                                        # commit() відбудеться в db_log
        else:                                                                         # список [table_data] - порожній
            return False
    except Exception as err:
        db_error(err)
        return False
    return True


def db_update(table_query, table_data) -> any:
    """ Updates rows in a table """
    try:
        cur.execute(table_query, table_data)
        con.commit()
        return cur.rowcount                                                      # кількість оновлених записів
    except Exception as err:
        db_error(err)
        return None


def db_delete(table_name: str = "", table_where: str = "") -> bool:
    """ Delete a row from a database table """
    try:
        cur.execute(f"DELETE FROM {table_name} WHERE {table_where}")            # WHERE rowid in (2,4) - 2,4 рядок
        con.commit()
        return True
    except Exception as err:
        db_error(err)
        return False


def db_error(err: Exception) -> None:
    """ Printing information about the module errors """
    # db_log(lines=('error', '', f"Error in module [{inspect.stack()[1][3]}]. [{err}]"))
    db_log(('error', '', f'Error in module [{inspect.stack()[1][3]}]. [{err}]'))
    return None


def db_log(lines: tuple | list, print_enable=True, log_enable=True) -> bool:
    """ Log output to the screen and to the database """
    try:
        if not isinstance(lines, (tuple, list)):
            raise Exception(f"Wrong type of variable [lines] [{type(lines)}]")
        for _ in lines if isinstance(lines, list) else [lines]:                          # tuple --> to list(tuple)
            if print_enable:
                # print(f"{color_log.get(_[0].lower(), Color.green)}{_[0]:<8} {_[1]:<20} {_[2]}{Color.end}")
                print(f'{_[0]:<8} {_[1]:<20} {color_log.get(_[0].lower(), Color.green)}{_[2]}{Color.end}')
            if log_enable:
                cur.execute("INSERT INTO log VALUES(?, ?, ?);", _)
                con.commit()
        return True
    except Exception as err:
        db_error(err)
        return False


def db_process(mode="update", key="parameters", data=None, print_enable=True) -> any:
    """ Saving in the table [process] the value of the parameters for restart """
    try:
        if mode == "update":
            if _ := db_update(table_query=f"UPDATE process SET process_data=? WHERE process_key=? ",
                              table_data=(pickle.dumps(data), key)):
                db_log(('process', '', f'Table [process] Updating rows:  {_}'), print_enable=print_enable)
            elif _ := db_insert(table_query=f"INSERT INTO process (process_key, process_data) VALUES (?, ?) ",
                                table_data=(key, pickle.dumps(data))):
                db_log(('process', '', f'Table [process] Inserting rows: {_}'), print_enable=print_enable)
            else:
                return None
        elif mode == "select":
            if _ := db_select(table_query=f"SELECT process_data FROM process WHERE process_key='{key}'"):
                db_log(('process', '', f'Table [process] Selected rows:  {len(_)}'), print_enable=print_enable)
                return pickle.loads(_[0][0])
            else:
                if print_enable:
                    db_log(('process', '', f'Table [process] Selected rows: {Color.red}0'), print_enable=print_enable)
    except Exception as err:
        db_error(err)
    return None


# ********************************************************************
con = sqlite3.connect(Settings.db_file)
cur = con.cursor()
db_start()
