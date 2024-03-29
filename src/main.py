import logging
import re
from collections import Counter
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, EXPECTED_STATUS, MAIN_DOC_URL, PEP_URL
from outputs import control_output
from utils import find_tag, get_response


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
        )

    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append(
            (version_link, h1.text, dl_text)
        )

    return results


def latest_versions(session):
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')

    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            raise Exception('Ничего не нашлось')
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'

    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version = text_match.group(1)
            status = text_match.group(2)
        else:
            version, status = a_tag.text, ''
        results.append(
                (link, version, status)
            )

    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    main_tag = find_tag(soup, 'div', {'role': 'main'})
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})
    pdf_a4_tag = find_tag(
        table_tag, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')}
        )
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    downloads = 'downloads'
    downloads_dir = BASE_DIR / downloads
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = get_response(session, archive_url)
    if response is None:
        return

    with open(archive_path, 'wb') as file:
        file.write(response.content)
        logging.info(f'Файл загружен. Путь: {archive_path}')


def pep(session):
    results = [('Статус', 'Количество')]
    response = get_response(session, PEP_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    pep_content = find_tag(soup, 'section', attrs={'id': 'pep-content'})
    numerical_index = find_tag(
        pep_content, 'section', {'id': 'numerical-index'}
        )
    tbody = find_tag(numerical_index, 'tbody')
    tr_tags = tbody.find_all('tr')
    status_list = []
    total_pep = 0

    for tr_tag in tr_tags:

        # Собираем информацию из таблицы
        a_tag = find_tag(tr_tag, 'a')
        abbr_tag = find_tag(tr_tag, 'abbr')
        table_status = abbr_tag.text[1:]
        pep_link = a_tag['href']
        full_link = urljoin(PEP_URL, pep_link)

        # Собираем информацию со страницы конкретного PEP
        response = get_response(session, full_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        pep_content = find_tag(soup, 'section', attrs={'id': 'pep-content'})
        dl_tag = find_tag(
            pep_content, 'dl', {'class', 'rfc2822 field-list simple'}
            )
        dtdd_tags = dl_tag.find_all()
        search_dt = False
        search_dd = False
        for tag in dtdd_tags:
            page_status = None
            if search_dd is True:
                page_status = tag.text
                status_list.append(page_status)
                total_pep += 1
                if page_status not in EXPECTED_STATUS[table_status]:
                    error_msg = (f'Несовпадающие статусы:\n'
                                 f'{full_link}\n'
                                 f'Статус в карточке: {page_status}\n'
                                 f'Ожидаемые статусы: '
                                 f'{EXPECTED_STATUS[table_status]}')
                    logging.warning(error_msg)
                break
            else:
                if search_dt is True:
                    search_dd = True
            if tag.text == 'Status:':
                search_dt = True
            else:
                continue
    counter = dict(Counter(status_list))
    for status, count in counter.items():
        results.append(
            (status, count)
        )
    results.append(
        ('Total', total_pep)
    )
    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
        logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
