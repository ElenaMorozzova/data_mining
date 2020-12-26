import scrapy
import json
import datetime as dt
from scrapy.exceptions import CloseSpider
from ..items import InstaFollowed, InstaFollowing


class HandshakesSpider(scrapy.Spider):
    db_type = 'MONGO'
    name = 'insta_handshakes'
    allowed_domains = ['www.instagram.com']
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    start_urls = ['http://www.instagram.com/']

    query_hash = {
        'following': 'd04b0a864b4b54837c0d870b0e77e076',
        'followed': 'c76146de99bb02f6415203be841dd25a',
    }

    def __init__(self, login, password, *args, **kwargs):
        self.login = login
        self.password = password
        self.user_1 = 'm.a.rrr.t.a'
        self.user_2 = 'juice_berry'
        # shopping7772020 natalya_napylova  juice_berry
        self.user1_followed_by = []
        self.user1_following = []
        self.mutual_friends_level_1 = []
        super(HandshakesSpider, self).__init__(*args, **kwargs)

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
                yield response.follow(f'/{self.user_1}',
                                      callback=self.user_parse,
                                      cb_kwargs={'level': 1, 'mutual_follower': None})

    def user_parse(self, response, level, mutual_follower):
        user_data = self.js_data_extract(response)['entry_data']['ProfilePage'][0]['graphql']['user']
        print(f'Ищу среди друзей {mutual_follower}')
        yield from self.get_follow_request(response, user_data, level, mutual_follower)

    def get_follow_request(self, response, user_data, level, mutual_follower, follow_query=None):

        if not follow_query:
            follow_query = {
                'id': user_data['id'],
                'first': 50,
            }

        # Список подписчиков пользователя
        url_followed = f'/graphql/query/?query_hash={self.query_hash["followed"]}&variables={json.dumps(follow_query)}'
        yield response.follow(
            url_followed,
            callback=self.get_api_followed,
            cb_kwargs={'user_data': user_data, 'level': level, 'mutual_follower': mutual_follower})

        # Список подписок пользователя - после прохождения первого генератора
        url_following = f'/graphql/query/?query_hash={self.query_hash["following"]}&variables={json.dumps(follow_query)}'
        yield response.follow(
            url_following,
            callback=self.get_api_follow,
            cb_kwargs={'user_data': user_data, 'level': level, 'mutual_follower': mutual_follower})

    def get_api_follow(self, response, level, user_data, mutual_follower):
        data = response.json()
        follow_type = 'following'
        yield from self.get_follow_item(user_data,
                                        data['data']['user']['edge_follow']['edges'],
                                        follow_type,
                                        response,
                                        level,
                                        mutual_follower)
        if data['data']['user']['edge_follow']['page_info']['has_next_page']:
            follow_query = {
                'id': user_data['id'],
                'first': 50,
                'after': data['data']['user']['edge_follow']['page_info']['end_cursor'],
            }
            yield from self.get_follow_request(response, user_data, follow_query, level, mutual_follower)

    def get_api_followed(self, response, user_data, level, mutual_follower):
        data = response.json()
        follow_type = 'followed'
        yield from self.get_follow_item(user_data,
                                        data['data']['user']['edge_followed_by']['edges'],
                                        follow_type,
                                        response,
                                        level,
                                        mutual_follower)
        if data['data']['user']['edge_followed_by']['page_info']['has_next_page']:
            follow_query = {
                'id': user_data['id'],
                'first': 50,
                'after': data['data']['user']['edge_followed_by']['page_info']['end_cursor'],
            }
            yield from self.get_follow_request(response, user_data, follow_query, level, mutual_follower)

    def get_follow_item(self, user_data, follow_users_data, follow_type, response, level, mutual_follower):
        for user in follow_users_data:
            # исключаем аккаунты с закрытыми подписками и подтвержденные аккаунты (обычно имеют большое колличество односторонних followers)
            if follow_type == 'followed' and user['node']['is_private'] is False and user['node']['is_verified'] is False:
                yield InstaFollowed(
                    user_id=user_data['id'],
                    user_name=user_data['username'],
                    follow_type='followed_by',
                    follow_id=user['node']['id'],
                    follow_name=user['node']['username']
                )
                self.user1_followed_by.append(user['node']['username'])
            elif follow_type == 'following' and user['node']['is_private'] is False and user['node']['is_verified'] is False:
                yield InstaFollowing(
                    user_id=user_data['id'],
                    user_name=user_data['username'],
                    follow_type='following',
                    follow_id=user['node']['id'],
                    follow_name=user['node']['username']
                )
                self.user1_following.append(user['node']['username'])

        if len(self.user1_followed_by) >= 1 and len(self.user1_following) >= 1:
            self.mutual_friends_level_1 = list(set(self.user1_followed_by) & set(self.user1_following))
            if self.user_2 in self.mutual_friends_level_1 and level == 1:
                print(f'Пользователь {self.user_1} и {self.user_2} подписаны друг на друга, рукопожатие 1 уровня')

            elif self.user_2 in self.mutual_friends_level_1 and level > 1:
                print(f'Пользователь {self.user_1} и {self.user_2} знакомы друг с другом через пользователя {mutual_follower}')
                raise CloseSpider('found')
            else:
                level = level + 1
                print(f' Пользователи не подписаны друг на друга, поиск взаимных подписок пользователя из списка {self.mutual_friends_level_1}')
                for mutual_follower in self.mutual_friends_level_1:
                    mut_follower_url = 'http://www.instagram.com/' + mutual_follower
                    self.user1_followed_by = []
                    self.user1_following = []
                    yield response.follow(url=mut_follower_url, callback=self.user_parse, cb_kwargs={'mutual_follower': mutual_follower, 'level': level})
        else:
            pass

    def js_data_extract(self, response):
        script = response.xpath('//script[contains(text(), "window._sharedData = ")]/text()').get()
        return json.loads(script.replace("window._sharedData = ", '')[:-1])
