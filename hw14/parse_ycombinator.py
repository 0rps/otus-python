import random
import os
import shutil
import asyncio
import aiohttp
from html.parser import HTMLParser


MAIN_LOOP_SLEEP_TIME = 5


def download_delay():
    return random.random()


class YCombinatorMainPageParser(HTMLParser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._post_id = None
        self._posts = []

    @property
    def posts(self):
        return self._posts

    def feed(self, data):
        self._posts = []
        self._post_id = None
        super().feed(data)

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self._handle_tr(attrs)
        elif tag == 'a':
            self._handle_a(attrs)

    def _handle_tr(self, attrs):
        attrs_hash = {}
        for attr_tuple in attrs:
            attrs_hash[attr_tuple[0]] = attr_tuple

        if 'class' in attrs_hash and attrs_hash['class'][1] == 'athing':
            self._post_id = attrs_hash['id'][1]
        else:
            self._post_id = None

    def _handle_a(self, attrs):
        attrs_hash = {}
        for attr_tuple in attrs:
            attrs_hash[attr_tuple[0]] = attr_tuple

        if 'class' in attrs_hash and attrs_hash['class'][1] == 'storylink':
            self._posts.append({'id': self._post_id, 'href': attrs_hash['href'][1]})
            self._post_id = None


class YCombinatorCommentsPageParser(HTMLParser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._comment_id = 0
        self._comments = []
        self._is_comment_span = False

    @property
    def comments(self):
        return self._comments

    def feed(self, data):
        self._comment_id = 0
        self._comments = []
        self._is_comment_span = False
        super().feed(data)

    def handle_starttag(self, tag, attrs):
        if tag == 'span':
            for attr in attrs:
                if attr[0] == 'class' and attr[1] == 'commtext c00':
                    self._is_comment_span = True
        elif tag == 'a' and self._is_comment_span:
            self._handle_comment(attrs)

    def handle_endtag(self, tag):
        if tag == 'span' and self._is_comment_span:
            self._is_comment_span = False

    def _handle_comment(self, attrs):
        for attr in attrs:
            if attr[0] == 'href':
                self._comments.append({'id': self._comment_id, 'href': attr[1]})
                self._comment_id += 1


async def download_post_page(session: aiohttp.ClientSession, url: str, filepath: str):
    await asyncio.sleep(download_delay())

    async with session.get(url) as response:
        html = await response.text()

    with open(filepath, 'w') as f:
        f.write(html)


async def download_comments_page(session: aiohttp.ClientSession, url: str, comments_dir: str):
    await asyncio.sleep(download_delay())

    async with session.get(url) as response:
        html = await response.text()

    parser = YCombinatorCommentsPageParser()
    parser.feed(html)

    tasks = []

    if len(parser.comments) > 0:
        os.mkdir(comments_dir)

    for comment_data in parser.comments:
        href = comment_data['href']
        comment_file = os.path.join(comments_dir, "{}.html".format(comment_data['id']))
        tasks.append(download_comment(session, href, comment_file))

    await asyncio.wait([asyncio.ensure_future(x) for x in tasks])


async def download_comment(session: aiohttp.ClientSession, url: str, comment_file: str):
    await asyncio.sleep(download_delay())

    async with session.get(url) as response:
        html = await response.text()

    with open(comment_file, 'w') as f:
        f.write(html)


async def watch_main_page(url: str, workpath: str):
    downloaded = set()
    session = aiohttp.ClientSession()

    while True:
        async with session.get(url) as response:
            html = await response.text()

        parser = YCombinatorMainPageParser()
        parser.feed(html)

        tasks = []
        for post in parser.posts:
            if post['id'] in downloaded:
                continue
            downloaded.add(post['id'])

            post_filepath = os.path.join(workpath, '{}.html'.format(post['id']))
            tasks.append(download_post_page(session, post['href'], post_filepath))

            comments_url = "https://news.ycombinator.com/item?id={}".format(post['id'])
            comments_path = os.path.join(workpath, post['id'])
            tasks.append(download_comments_page(session, comments_url, comments_path))

        if len(tasks) > 0:
            await asyncio.wait([asyncio.ensure_future(x) for x in tasks])

        print('Tasks loop step, {} new acticles'.format(len(tasks)))

        await asyncio.sleep(MAIN_LOOP_SLEEP_TIME)


if __name__ == "__main__":
    workpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ycombinator')
    shutil.rmtree(workpath, ignore_errors=True)
    os.mkdir(workpath)

    ioloop = asyncio.get_event_loop()
    tasks = [ioloop.create_task(watch_main_page('https://news.ycombinator.com', workpath))]
    wait_tasks = asyncio.wait(tasks)

    ioloop.run_until_complete(wait_tasks)
    ioloop.close()
