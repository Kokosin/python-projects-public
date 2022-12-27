from bs4 import BeautifulSoup
from datetime import datetime
import re
from module_functions import requests_get, is_module_started
from module_settings import Settings
from module_db_sqlite import db_insert_many, db_close, db_process, db_log


# *****************************************************************
def main() -> any:
    """ Processing the all posts and releases """
    is_module_started(main.__doc__)

    # ------------------------------------------------------------ блок - старт з початку або з точки зупинки
    url_page_next, num_page, num_post = _ if (_ := db_process(mode="select", key="parameters")) \
        else (Settings.url_page, 0, 0)

    db_log(('process' if not num_page else 'warning', '',
            f'{"Start" if not num_page else "Continue"} process. Page: {num_page} Post: {num_post}'))
    db_log(('info', '', f"url: {url_page_next}"))
    # ------------------------------------------------------------

    while url_page_next:
        response_value, response_log = requests_get(url=url_page_next)         # отримуємо нову сторінку з постами
        if not response_value:                                                 # ... остання сторінка або error !!!
            return response_log                                                # critical or error - відсутній інтернет

        soup = BeautifulSoup(response_value.text, 'lxml')
        url_page_next = _.get('href') if (_ := soup.find('a', class_='blog-pager-older-link')) else ''

        result = dict(post=list(),
                      release=list(),
                      release_table=list(),
                      log=list())
        num_page += 1

        for post in soup.find_all('div', class_='date-outer'):               # список постів на сторінці (6-7)
            num_post += 1
            item = dict()                                                    # словник - вибрані поля з посту
            release_urls = list()                                            # список релізів [urls] з посту

            log = [('info', '', f"{'-' * 50} Page: {num_page} Post: {num_post}")]

            for key in ['p_id', 'p_url', 'p_date', 'p_title', 'p_author', 'p_content', 'p_releases']:
                try:
                    element = ''
                    match key:
                        case 'p_id':     # '6363800878405663863'
                            element = _[0].find('a').get('name') \
                                if (_ := post.find_all('div', class_='post hentry')) else ''
                        case 'p_url':
                            element = _.find('a').get('href') \
                                if (_ := post.find('h3', class_='post-title entry-title')) else ''
                        case 'p_date':   # 'Wednesday, December 8, 2021'
                            element = _.text if (_ := post.find('h2', class_='date-header')) else ''
                        case 'p_title':  # 'Python 3.10.2, 3.9.10, and 3.11.0a4 are now available'
                            element = _.text if (_ := post.find('h3', class_='post-title entry-title')) else ''
                        case 'p_author':  # 'Pablo Galindo'
                            element = _.text if (_ := post.find('span', class_='fn')) else ''
                        case 'p_content':
                            element = _.text if (_ := post.find('div', class_='post-body entry-content')) else ''
                            if not element:
                                element = _.text if (_ := post.find('div', class_='gmail_default')) else ''
                        case 'p_releases':  # ['https://www.python.org/downloads/release/python-3910/',...,...]
                            element = list()
                            for find_str in ["/downloads/release/", "download/releases/"]:
                                element += list({_.get('href').strip()
                                                 for _ in post.find_all(href=re.compile(find_str)) if _})
                            release_urls = element
                            element = ','.join(element) if element else ''

                    item[key] = _ if (_ := element.strip()) else ''
                    log.append(('debug', key, _[:90].replace('\n', ' ').strip()) if _ else
                               ('warning', key, "<--- not found"))
                except Exception as err:
                    item[key] = ''
                    log.append(('error', key, f"<--- not found [{err}]"))

            result['post'].append(tuple(item.values()))
            result['log'] += log
            db_log(log)

            # ------------------------------------------------------ releases in post
            for release_url in release_urls:

                response_value, response_log = requests_get(url=release_url)
                if not response_value:
                    if response_log[0] == 'critical':                                    # відсутній інтернет
                        return response_log
                    else:
                        result['log'].append(response_log)                               # відсутній реліз
                        db_log(response_log)
                        continue

                log = [('info', '', f"{'-' * 50}")]
                soup = BeautifulSoup(response_value.text, 'lxml')

                item = dict()

                for key in ['r_url', 'r_date', 'r_title', 'r_h1', 'r_content', 'r_peps']:
                    try:
                        element = ''
                        match key:
                            case 'r_url':
                                element = release_url
                            case 'r_date':   # 'Release Date: Jan. 14, 2022' --> ['Jan. 14, 2022'] --> 'Jan. 14, 2022'
                                element = soup.find('section').find_all('p')[0].text
                                element = element.split(':')[1] if element and 'Release Date:' in element else ''
                            case 'r_title':  # 'This is an early developer preview of Python 3.11'
                                element = _.text if (_ := soup.find('h2')) else ''
                                if not element:
                                    element = _.find_all('p')[1].text if (_ := soup.find('section')) else ''
                            case 'r_h1':    # 'Python 3.9.10'
                                element = _.text if (_ := soup.find('h1', class_='page-title')) else ''
                            case 'r_content':
                                element = _.text if (_ := soup.find('article', class_='text')) else ''
                                element = element[:_] if (_ := element.find('\nFiles\n')) != -1 else element
                            case 'r_peps':
                                element = [_.strip() for _ in re.findall(r'>PEP (.*?)<', response_value.text, re.DOTALL)
                                           if _ and _.strip().isdigit()]
                                element = ",".join(sorted(list(set(element)))) if element else ''

                        item[key] = _ if (_ := element.strip()) else ''
                        log.append(('debug', key, _[:90].replace('\n', ' ').strip()) if _ else
                                   ('warning', key, "<--- not found"))
                    except Exception as err:
                        item[key] = ''
                        log.append(('error', key, f"<--- not found [{err}]"))
                # -------------------------------------------------------- table
                soup_table = BeautifulSoup(response_value.text, 'lxml').find('table')
                if not soup_table:
                    result['log'].append(('warning', '', 'Table not found in release'))
                else:
                    try:
                        table_row = 0
                        # th = [x.text for x in soup_table.find_all('th')]
                        for table_row, tr in enumerate(soup_table.find_all('tr')):
                            if table_row > 0:
                                table_line = [''] * 8                                    # може бути максимум 8 колонок
                                for table_col, td in enumerate(tr.find_all('td')):
                                    table_line[table_col] = \
                                        (str([f"{td.text}", _.get('href') if (_ := td.find('a')) else '']))
                                result['release_table'].append(tuple([item['r_url']] + table_line))
                        log.append(('debug', '', f"Table parsing. Rows inserted [{table_row}]"))
                    except Exception as err:
                        log.append(('error', '', f"Table parsing. Error [{err}]"))
                # -------------------------------------------------------- end -- table
                result['release'].append(tuple(item.values()))
                result['log'] += log
                db_log(log)
        # ---------------------------------------------------------------- зберігаємо в таблиці БД
        for table_name in ['post', 'release']:
            db_insert_many(mode="execute", table_name=table_name, table_data=result[table_name])
        for table_name in ['release_table', 'log']:
            db_insert_many(mode="executemany", table_name=table_name, table_data=result[table_name])

        db_process(mode="update", key="parameters", data=(url_page_next, num_page, num_post), print_enable=False)
    # ----------------------------------------------------------
    return None
# --------------------------------------------------------------


# **************************************************************
if __name__ == "__main__":

    db_log(('process', '', f'{"-" * 50} Start process: [{str(datetime.now())[:-7]}]'))
    db_log(('process', '', f'Site scraping protocol [{Settings.url_page}].'))

    _response_value, _response_log = requests_get(Settings.url_page)
    if not _response_value:                                                                     # відсутній інтернет
        db_log(_response_log)
    else:
        if (_ := main()) and _[0] in ['critical', 'error']:
            db_log(_)
            db_log(('warning', '', 'An error occurred while generating the database. You can restart the process.'))

    db_log(('process', '', 'Program completed. The SqLite database is closed.'))
    db_log(('process', '', f'{"-" * 50} End process: [{str(datetime.now())[:-7]}]'))
    db_close(print_enable=False)
