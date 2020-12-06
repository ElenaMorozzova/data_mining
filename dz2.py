import os
import time
import requests
import bs4
import pymongo
import dotenv
from urllib.parse import urljoin
import arrow

dotenv.load_dotenv('.env')


class MagnitParse:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0'
    }

    def __init__(self, start_url):
        self.start_url = start_url
        client = pymongo.MongoClient(os.getenv('DATA_BASE'))
        # client = "mongodb://localhost:27017"
        self.db = client['myparse_db']

        self.product_template = {
            'url': lambda soup: urljoin(self.start_url, soup.get('href')),
            'promo_name': lambda soup: soup.find('div', attrs={'class': 'card-sale__header'}).text,
            'product_name': lambda soup: soup.find('div', attrs={'class': 'card-sale__title'}).text,
            'image_url': lambda soup: urljoin(self.start_url, soup.find('img').get('data-src')),
            'old_price': lambda soup: float(soup.find('div', attrs={'class': 'label__price label__price_old'}).find('span', attrs={'class': 'label__price-integer'}).text +
                                            '.' + soup.find('div', attrs={'class': 'label__price label__price_old'}).find('span', attrs={'class': 'label__price-decimal'}).text),
            'new_price': lambda soup: float(soup.find('div', attrs={'class': 'label__price label__price_new'}).find('span', attrs={'class': 'label__price-integer'}).text +
                                            '.' + soup.find('div', attrs={'class': 'label__price label__price_new'}).find('span', attrs={'class': 'label__price-decimal'}).text),
            'date_from': lambda soup: self.to_date(" ".join(soup.find('div', attrs={'class': 'card-sale__date'}).find_all('p')[0].text.split()[1:])),
            'date_to': lambda soup: self.to_date(" ".join(soup.find('div', attrs={'class': 'card-sale__date'}).find_all('p')[1].text.split()[1:]))
        }

    @staticmethod
    def _get(*args, **kwargs):
        while True:
            try:
                response = requests.get(*args, **kwargs)
                if response.status_code != 200:
                    raise Exception
                return response
            except Exception:
                time.sleep(0.5)

    @staticmethod
    def to_date(string_date):
        if string_date.split()[1] in ('Ноября', 'ноября', 'Декабря', 'декабря'):
            converted_date = arrow.get(string_date, 'D MMMM', locale='ru').format('2020-MM-DD')
        else:
            converted_date = arrow.get(string_date, 'D MMMM', locale='ru').format('2021-MM-DD')
        return converted_date

    def soup(self, url) -> bs4.BeautifulSoup:
        response = self._get(url, headers=self.headers)
        return bs4.BeautifulSoup(response.text, 'lxml')

    def run(self):
        soup = self.soup(self.start_url)
        for product in self.parse(soup):
            self.save(product)

    def parse(self, soup):
        catalog = soup.find('div', attrs={'class': 'сatalogue__main'})

        for product in catalog.find_all('a', recursive=False):
            pr_data = self.get_product(product)
            yield pr_data

    def get_product(self, product_soup) -> dict:
        result = {}
        for key, value in self.product_template.items():
            try:
                result[key] = value(product_soup)
            except Exception as e:
                continue
        return result

    def save(self, product):
        collection = self.db['magnit']
        collection.insert_one(product)


if __name__ == '__main__':
    parser = MagnitParse('https://magnit.ru/promo/?geo=moskva')
    parser.run()
