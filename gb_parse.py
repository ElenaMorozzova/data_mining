import bs4
import requests
from urllib.parse import urljoin
from database import DataBase


class GbBlogParse:
    _headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0'
    }

    def __init__(self, start_url: str, db: DataBase):
        self.start_url = start_url
        self.page_done = set()
        self.db = db

    def __get(self, url) -> bs4.BeautifulSoup:
        response = requests.get(url)
        self.page_done.add(url)
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        return soup

    def run(self, url=None):
        if not url:
            url = self.start_url

        if url not in self.page_done:
            soup = self.__get(url)
            posts, pagination = self.parse(soup)

            for post_url in posts:
                page_data = self.page_parse(self.__get(post_url), post_url)
                self.save(page_data)
            for p_url in pagination:
                self.run(p_url)

    def parse(self, soup):
        ul_pag = soup.find('ul', attrs={'class': 'gb__pagination'})
        paginations = set(
            urljoin(self.start_url, url.get('href')) for url in ul_pag.find_all('a') if url.attrs.get('href'))
        posts = set(
            urljoin(self.start_url, url.get('href')) for url in soup.find_all('a', attrs={'class': 'post-item__title'}))
        return posts, paginations

    def page_parse(self, soup, url) -> dict:
        data = {
            'post_data': {
                'url': url,
                'title': soup.find('h1').text,
                'image': soup.find('div', attrs={'class': 'blogpost-content'}).find('img').get('src') if soup.find(
                    'div', attrs={'class': 'blogpost-content'}).find('img') else None,
                'date': soup.find('div', attrs={'class': 'blogpost-date-views'}).find('time').get('datetime'),
            },
            'writer': {'name': soup.find('div', attrs={'itemprop': 'author'}).text,
                       'url': urljoin(self.start_url,
                                      soup.find('div', attrs={'itemprop': 'author'}).parent.get('href'))},

            'tags': [],
            'comments': [],

        }
        for tag in soup.find_all('a', attrs={'class': "small"}):
            tag_data = {
                'url': urljoin(self.start_url, tag.get('href')),
                'name': tag.text
            }
            data['tags'].append(tag_data)

        for page in soup.find_all('div', attrs={'class': 'referrals-social-buttons-small-wrapper'}):
            comment_api = 'https://geekbrains.ru/api/v2/comments?commentable_type=Post&commentable_id='
            page_id = soup.find('div', attrs={'class': 'referrals-social-buttons-small-wrapper'}).get('data-minifiable-id')
            comment_url = comment_api + page_id
            response = requests.get(comment_url, headers=self._headers)
            json_response = response.json()
            if len(json_response) == 0:
                comment_data = {
                    'url': comment_url,
                    'author': None,
                    'text': None
                }
            else:
                comment_data = {
                    'url': comment_url,
                    'author': json_response[0]["comment"]["user"]["full_name"],
                    'text': json_response[0]["comment"]["html"]
                }
                data['comments'].append(comment_data)
                if len(json_response[0]["comment"]["children"]) == 0:
                    pass
                else:
                    comment_data = {
                        'url': comment_url,
                        'author': json_response[0]["comment"]["children"][0]["comment"]["user"]["full_name"],
                        'text': json_response[0]["comment"]["children"][0]["comment"]["html"]
                    }
                data['comments'].append(comment_data)

        return data

    def save(self, page_data: dict):
        self.db.create_post(page_data)


if __name__ == '__main__':
    db = DataBase('sqlite:///gb_blog.db')
    parser = GbBlogParse('https://geekbrains.ru/posts', db)
    parser.run()
