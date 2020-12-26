import json
import scrapy
import datetime as dt
from ..loaders import HhruLoader
from ..items import InstaTag, InstaPost, InstaUser, InstaFollowed


class InstagramSpider(scrapy.Spider):
    db_type = 'MONGO'
    name = 'instagram'
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']

    query_hash = {
        'tag_post': '9b498c08113f1e09617a1703c22b2f32',
        'following': 'd04b0a864b4b54837c0d870b0e77e076',
        'followed': 'c76146de99bb02f6415203be841dd25a',
    }

    def __init__(self, login, password, tag_list, user_list, *args, **kwargs):
        self.login = login
        self.password = password

        self.tag_list = tag_list
        self.user_list = user_list
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
                # for tag in self.tag_list:
                #     yield response.follow(f'/explore/tags/{tag}', callback=self.tag_parse)
                for user in self.user_list:
                    yield response.follow(f'/{user}', callback=self.user_parse)

    def user_parse(self, response):
        user_data = self.js_data_extract(response)['entry_data']['ProfilePage'][0]['graphql']['user']
        yield InstaUser(
            date_parse=dt.datetime.utcnow(),
            data=user_data
        )

        yield from self.get_follow_request(response, user_data)

    def get_follow_request(self, response, user_data, follow_query=None):
        if not follow_query:
            follow_query = {
                'id': user_data['id'],
                'first': 2,
            }

        # Список подписчиков пользователя
        url = f'/graphql/query/?query_hash={self.query_hash["followed"]}&variables={json.dumps(follow_query)}'
        yield response.follow(
            url,
            callback=self.get_api_followed,
            cb_kwargs={'user_data': user_data})

        # # Список подписок пользователя
        # url = f'/graphql/query/?query_hash={self.query_hash["following"]}&variables={json.dumps(follow_query)}'
        # yield response.follow(
        #     url,
        #     callback=self.get_api_follow,
        #     cb_kwargs={'user_data': user_data})

    def get_api_follow(self, response, user_data):
        data = response.json()
        follow_type = 'following'
        yield from self.get_follow_item(user_data,
                                        data['data']['user']['edge_follow']['edges'],
                                        follow_type)
        if data['data']['user']['edge_follow']['page_info']['has_next_page']:
            follow_query = {
                'id': user_data['id'],
                'first': 100,
                'after': data['data']['user']['edge_follow']['page_info']['end_cursor'],
            }
            yield from self.get_follow_request(response, user_data, follow_query)

    def get_api_followed(self, response, user_data):
        data = response.json()
        follow_type = 'followed'
        yield from self.get_follow_item(user_data,
                                        data['data']['user']['edge_followed_by']['edges'],
                                        follow_type)
        if data['data']['user']['edge_followed_by']['page_info']['has_next_page']:
            follow_query = {
                'id': user_data['id'],
                'first': 100,
                'after': data['data']['user']['edge_followed_by']['page_info']['end_cursor'],
            }
            yield from self.get_follow_request(response, user_data, follow_query)

    def get_follow_item(self, user_data, follow_users_data, follow_type):
        for user in follow_users_data:
            if follow_type == 'followed':
                yield InstaFollow(
                    user_id=user_data['id'],
                    user_name=user_data['username'],
                    follow_type='followed_by',
                    follow_id=user['node']['id'],
                    follow_name=user['node']['username']
                )
            else:
                yield InstaFollow(
                    user_id=user_data['id'],
                    user_name=user_data['username'],
                    follow_type='following',
                    follow_id=user['node']['id'],
                    follow_name=user['node']['username']
                )
            yield InstaUser(
                date_parse=dt.datetime.utcnow(),
                data=user['node']
            )

    def js_data_extract(self, response):
        script = response.xpath('//script[contains(text(), "window._sharedData = ")]/text()').get()
        return json.loads(script.replace("window._sharedData = ", '')[:-1])

    # def tag_parse(self, response):
    #     tag_data = self.js_data_extract(response)['entry_data']['TagPage'][0]['graphql']['hashtag']
    #     yield InstaTag(
    #         date_parse=dt.datetime.utcnow(),
    #         data={
    #             'id': tag_data['id'],
    #             'name': tag_data['name'],
    #             'profile_pic_url': tag_data['profile_pic_url'],
    #             'count': tag_data['edge_hashtag_to_media']['count'],
    #         }
    #     )
    #     yield from self.get_tag_posts(tag_data, response)
    #
    # def get_tag_posts(self, tag_data, response):
    #     if tag_data['edge_hashtag_to_media']['page_info']['has_next_page']:
    #         api_query = {
    #             'tag_name': tag_data['name'],
    #             'first': 2,
    #             'after': tag_data['edge_hashtag_to_media']['page_info']['end_cursor'],
    #         }
    #         url = f'/graphql/query/?query_hash={self.query_hash["tag_post"]}&variables={json.dumps(api_query)}'
    #         yield response.follow(
    #             url,
    #             callback=self.tag_api_parse,
    #         )
    #     yield from self.get_post_item(tag_data['edge_hashtag_to_media']['edges'])
    #
    # def get_post_item(self, edges, **kwargs):
    #     for node in edges:
    #         yield InstaPost(
    #             date_parse=dt.datetime.utcnow(),
    #             data=node['node'],
    #             image_urls=[node['node']['thumbnail_src']]
    #         )
    #
    # def tag_api_parse(self, response, **kwargs):
    #     yield from self.get_tag_posts(response.json()['data']['hashtag'], response) #
