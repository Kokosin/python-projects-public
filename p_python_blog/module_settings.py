from pathlib import Path

db_structure = """
CREATE TABLE IF NOT EXISTS process (
process_key TEXT PRIMARY KEY,
process_data TEXT); 

CREATE TABLE IF NOT EXISTS post (
p_id TEXT PRIMARY KEY,
p_url TEXT,
p_date TEXT,
p_title TEXT,
p_author TEXT,
p_content TEXT,
p_release TEXT);

CREATE TABLE IF NOT EXISTS release (
r_url TEXT PRIMARY KEY,
r_date TEXT,
r_title TEXT,
r_h1 TEXT,
r_content TEXT,
r_peps_list TEXT);

CREATE TABLE IF NOT EXISTS release_table (
r_url TEXT,
r_Version TEXT,
r_Operating_System TEXT,
r_Description TEXT,
r_MD5_Sum TEXT,
r_File_Size TEXT,
r_GPG TEXT,
r_SigStore_CRT TEXT,
r_SigStore_SIG TEXT);

CREATE TABLE IF NOT EXISTS log (
e_level TEXT,
e_value TEXT,
e_line TEXT); 
"""


class Settings:
    url_page = "https://blog.python.org/"
    db_file = 'python_blog.db'
    db_path = Path.cwd()
    # file_post = '_post.pickle'
    # file_urls = '_urls.pickle'
    # file_release = '_release.pickle'
    # mode_release = 'one process'               # 'one process' or 'multiprocessing'


class Color:
    end = '\033[0m'
    black = '\033[30m'
    red = '\033[31m'     # "\x1b[91m"
    green = '\033[32m'   # "\x1b[92m"
    yellow = '\033[33m'  # "\x1b[93m"
    blue = '\033[34m'
    purple = '\033[35m'
    cyan = '\033[36m'
    white = '\033[37m'
    grey = '\033[90m'


color_log = dict(
    debug=Color.grey,
    info=Color.white,
    process=Color.green,
    critical=Color.red,
    error=Color.red,
    warning=Color.yellow)
