import json
import scrapy
import datetime as dt
from ..loaders import HhruLoader
from ..items import InstaTag, InstaPost


class InstagramSpider(scrapy.Spider):
    db_type = 'MONGO'
    name = 'instagram'
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']

    query_hash = {
        'tag_post': '9b498c08113f1e09617a1703c22b2f32'
    }

    def __init__(self, login, password, tag_list, *args, **kwargs):
        self.login = login
        self.password = password

        self.tag_list = tag_list
        super(InstagramSpider, self).__init__(*args, **kwargs)

    def parse(self, response, **kwargs):
        try:
            js_data = self.js_data_extract(response)
            yield scrapy.FormRequest(
                self.login_url,
                method='POST',
                callback=self.parse,
                formdata={
                    'username': self.login,
                    'enc_password': self.password,
                },
                headers={'X-CSRFToken': js_data['config']['csrf_token']}
            )
        except AttributeError:
            if response.json().get('authenticated'):
                for tag in self.tag_list:
                    yield response.follow(f'/explore/tags/{tag}', callback=self.tag_parse)

    def tag_parse(self, response):
        tag_data = self.js_data_extract(response)['entry_data']['TagPage'][0]['graphql']['hashtag']
        yield InstaTag(
            date_parse=dt.datetime.utcnow(),
            data={
                'id': tag_data['id'],
                'name': tag_data['name'],
                'profile_pic_url': tag_data['profile_pic_url'],
                'count': tag_data['edge_hashtag_to_media']['count'],
            }
        )
        yield from self.get_tag_posts(tag_data, response)

    def get_tag_posts(self, tag_data, response):
        if tag_data['edge_hashtag_to_media']['page_info']['has_next_page']:
            api_query = {
                'tag_name': tag_data['name'],
                'first': 2,
                'after': tag_data['edge_hashtag_to_media']['page_info']['end_cursor'],
            }
            url = f'/graphql/query/?query_hash={self.query_hash["tag_post"]}&variables={json.dumps(api_query)}'
            yield response.follow(
                url,
                callback=self.tag_api_parse,
            )
        yield from self.get_post_item(tag_data['edge_hashtag_to_media']['edges'])

    def get_post_item(self, edges, **kwargs):
        for node in edges:
            yield InstaPost(
                date_parse=dt.datetime.utcnow(),
                data=node['node'],
                image_urls=[node['node']['thumbnail_src']]
            )

    def tag_api_parse(self, response, **kwargs):
        yield from self.get_tag_posts(response.json()['data']['hashtag'], response)

    def js_data_extract(self, response):
        script = response.xpath('//script[contains(text(), "window._sharedData = ")]/text()').get()
        return json.loads(script.replace("window._sharedData = ", '')[:-1])
