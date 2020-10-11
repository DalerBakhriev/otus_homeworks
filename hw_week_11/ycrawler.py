import argparse
import asyncio
import os
import re
import logging
import urllib.parse as url_parse
from typing import Optional, Union

import aiohttp
import uvloop
from bs4 import BeautifulSoup

TARGET_URL = "https://news.ycombinator.com/"
NUM_TOP_URLS = 30
RESULTS_ROOT_DIR = "./parsing_results"
COMMENTS_PATTERN = re.compile("comments")
DEFAULT_DOWNLOADING_PERIOD_SECONDS = 30
MAX_REDIRECTS_NUMBER = 30

def make_directory_name(url: str) -> str:

    """
    Makes folder name for giver url
    :param url: url to get folder name for
    :return directory (url without scheme name and extension)
    """

    directory_name = make_file_name_from_url(url)
    final_dir_name = directory_name.replace("/", "_")

    return os.path.join(RESULTS_ROOT_DIR, final_dir_name)


async def fetch(session: aiohttp.ClientSession, url: str) -> Union[bytes, Optional[str]]:

    """
    Fetch page with given url
    :param session: client session
    :param url: url to get page from
    :return: page text or bytes or None if some errors occcured during parsing
    """

    response_res = None
    try:
        async with session.get(url, max_redirects=MAX_REDIRECTS_NUMBER) as response:

            logging.debug("Got response contet type %s for url %s", response.content_type, url)
            
            if response.content_type == "text/html":
                response_res = await response.text()
            else:
                response_res = await response.read()

    except (aiohttp.ClientResponseError, aiohttp.ClientError):
        logging.exception("Something went wrong during parsing %s", url)
        pass

    return response_res

def save_page(page_for_saving: str, dir_name: str) -> None:

    """
    Saves given page in giver directory with name 'page.html'
    :param page_for_saving: page for saving
    :param dir_name: directory where given page should be saved
    """

    path_for_writing = os.path.join(dir_name, "page.html")
    with open(path_for_writing, "w") as page_write_file:
        page_write_file.write(page_for_saving)

def make_file_name_from_url(url: str) -> str:

    """
    Makes file name from url
    :param url: url of page that should be downloaded
    :return file name: name of file to save
    """

    clear_url = url_parse.urlparse(url)
    path, _ = os.path.splitext(clear_url.path)
    file_name = "".join((clear_url.netloc, path))

    return file_name

async def save_comments_page(session: aiohttp.ClientSession,
                             url: str,
                             dir_name: str) -> None:

    """
    Gets comment page from link
    and saves it to directory
    :param session: aiohttp client session
    :param url: comment url
    :param dir_name: directory name to save comment in
    """

    comment_page = await fetch(session, url)
    if comment_page is None:
        return

    file_name = make_file_name_from_url(url)
    final_file_name = ".".join([file_name.replace("/", "_"), "html"])

    path_for_saving = os.path.join(dir_name, final_file_name)
    writing_mode = "wb" if isinstance(comment_page, bytes) else "w"
    with open(path_for_saving, writing_mode) as comment_page_file:
        comment_page_file.write(comment_page)


async def fetch_and_save_comments(session: aiohttp.ClientSession, url: str, comments_dir: str) -> None:

    """
    Fetches all pages with links from news comments
    and saves them in news' directory
    :param session: client session
    :param url: news' url
    """

    comments_page = await fetch(session, url)
    comments_for_parsing = BeautifulSoup(comments_page, "html.parser")
    all_comments_tags = comments_for_parsing.find_all("tr", class_="athing comtr")

    for comment_tag in all_comments_tags:
        
        potential_links_tags = comment_tag.find_all("p")
        for potential_link_tag in potential_links_tags:

            link_tags = potential_link_tag.find_all("a", href=is_not_reply_link)
            if not link_tags:
                continue
            
            for link_tag in link_tags:
                link = link_tag.get("href")
                if not link:
                    continue
                await save_comments_page(session, link, comments_dir)


def is_not_reply_link(link: str) -> bool:

    """
    Return True if link is for reply and False otherwise
    """

    return not link.startswith("reply")

def make_directory(dir_name: str) -> None:

    """
    Makes directory in file system if it doesn't exist
    """
    
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)


def make_comments_dir(dir_name: str) -> str:

    comments_dir = os.path.join(dir_name, "comments")
    make_directory(comments_dir)
    
    return comments_dir


async def fetch_and_save_pages(news_links_limit: int) -> None:

    async with aiohttp.ClientSession() as session:

        html = await fetch(session, TARGET_URL)
        soup = BeautifulSoup(html, "html.parser")
        found_tags_for_title = soup.find_all("tr", class_="athing", limit=news_links_limit)
        found_tags_for_comments = soup.find_all("td", class_="subtext", limit=news_links_limit)
        number_of_pages_for_parsing = len(found_tags_for_title)
        logging.info("Going to parse %d pages with comments", number_of_pages_for_parsing)

        already_parsed_pages_number = 0
        for title_link_tag, comments_link_tag in zip(found_tags_for_title, found_tags_for_comments):

            logging.info("Started to parse page %d of %d", already_parsed_pages_number + 1, number_of_pages_for_parsing)
            title = title_link_tag.find(class_="storylink")
            source_page_url = title.get("href")
            if not source_page_url:
                already_parsed_pages_number += 1
                continue

            dir_name = make_directory_name(source_page_url)
            if os.path.exists(dir_name):
                already_parsed_pages_number += 1
                logging.info("Directory %s already exists. Stopping parsing.", dir_name)
                continue
            make_directory(dir_name)

            source_page = await fetch(session, source_page_url)
            if not source_page:
                already_parsed_pages_number += 1
                logging.error("Failed parsing page with url %s", source_page_url)
                continue
            save_page(source_page, dir_name)

            comments_dir = make_comments_dir(dir_name)
            comments_tag = comments_link_tag.find("a", string=COMMENTS_PATTERN)
            if not comments_tag:
                already_parsed_pages_number += 1
                logging.info("Comments not found for url: %s", source_page_url)
                continue

            comments_link_part = comments_tag.get("href")
            if not comments_link_part:
                already_parsed_pages_number += 1
                logging.info("Link for comment on url %s not found")
                continue

            comments_full_link = os.path.join(TARGET_URL, comments_link_part)
            await fetch_and_save_comments(session, comments_full_link, comments_dir)
            already_parsed_pages_number += 1
            logging.info("Successfully parsed page %d of %d", already_parsed_pages_number, number_of_pages_for_parsing)

async def run_page_parsing(news_links_limit: int, period: int) -> None:

    """
    Starts periodically parsing for target url
    with specified top news limit and period
    :param news_links_limit: number of top new which should be parsed
    :param period: period for checking some new news
    """

    while True:
        await fetch_and_save_pages(news_links_limit)
        logging.info("Waiting for %d seconds", period)
        await asyncio.sleep(period)



if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--period", type=int, default=DEFAULT_DOWNLOADING_PERIOD_SECONDS, help="Upgrading period")
    arg_parser.add_argument("--links-limit", type=int, default=NUM_TOP_URLS, help="Number of top links to be downloaded")
    arg_parser.add_argument("--debug", action="store_true", default=False, help="Run in debug mode")
    args = arg_parser.parse_args()

    logging.basicConfig(
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
        level=logging.DEBUG if args.debug else logging.INFO
    )
    logging.info("Started to parse %s with parameters %s", TARGET_URL, args)

    make_directory(RESULTS_ROOT_DIR)
    uvloop.install()
    asyncio.run(run_page_parsing(args.links_limit, args.period))
