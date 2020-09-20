import asyncio
import aiohttp
import urllib.parse as url_parse
from bs4 import BeautifulSoup
import os

TARGET_URL = "https://news.ycombinator.com/"
NUM_TOP_URLS = 30
RESULTS_ROOT_DIR = "./parsing_results"

def make_directory_name(url: str) -> str:

    """
    Makes folder name for giver url
    :param url: url to get folder name for
    :return directory (url without scheme name and extension)
    """

    clear_url = url_parse.urlparse(url)
    path, _ = os.path.splitext(clear_url.path)
    directory_name = "".join((clear_url.netloc, path))
    final_dir_name = directory_name.replace("/", "^")

    return os.path.join(RESULTS_ROOT_DIR, final_dir_name)

async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url) as response:
        return await response.text()

async def main():
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, TARGET_URL)
        soup = BeautifulSoup(html, "html.parser")
        found_tags = soup.find_all(attrs={"class": "storylink"}, limit=NUM_TOP_URLS)
        for tag in found_tags:
            href = tag["href"]
            dir_name = make_directory_name(href)
            os.mkdir(dir_name)


if __name__ == "__main__":
    if not os.path.exists(RESULTS_ROOT_DIR):
        os.mkdir(RESULTS_ROOT_DIR)
    asyncio.run(main())