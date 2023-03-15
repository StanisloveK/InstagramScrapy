import scrapy
from scrapy.http import HtmlResponse
import re
import json
from copy import deepcopy
from urllib.parse import urlencode
from instagram.items import InstagramItem


class InstagramSpiderSpider(scrapy.Spider):
    name = 'instagram_spider'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com/']
    url_link = 'https://www.instagram.com/accounts/login/ajax/'

    instagram_login = 'unforcer2409@mail.ru'
    instagram_password = ''
    users_parse = ['']

    mobile_user_agent = {'User-Agent': 'Instagram 155.0.0.37.107'}

    def parse(self, response: HtmlResponse):
        csrf = re.search('\\\\"csrf_token\\\\":\\\\"\w+\\\\"', response.text).group().split('\\')[-2].replace('"', '')
        yield scrapy.FormRequest(self.url_link,
                                 method='POST',
                                 callback=self.login,
                                 formdata={'username': self.instagram_login, 'enc_password': self.instagram_password},
                                 headers={'x-csrftoken': csrf})

    def login(self, response: HtmlResponse):
        j_data = response.json()
        if j_data.get('authenticated'):
            for self.user in self.users_parse:
                yield response.follow(f'/{self.user}/',
                                      callback=self.user_parsing,
                                      cb_kwargs={'username': self.user},
                                      headers=self.mobile_user_agent)

    def user_parsing(self, response: HtmlResponse, username):
        user_id = re.search(r'("id":")(\d+)(","profile_pic_url)', response.text).group(2)
        variables = {'count': 12}
        link_parse = [f'https://i.instagram.com/api/v1/friendships/{user_id}/followers/?{urlencode(variables)}&search_surface=follow_list_page',
                      f'https://i.instagram.com/api/v1/friendships/{user_id}/following/?{urlencode(variables)}']

        cb_kwargs_dict = {'username': username, 'user_id': user_id, 'variables': deepcopy(variables)}
        for link in link_parse:
            if 'followers' in link:
                yield response.follow(link,
                                      callback=self.followers_parse,
                                      cb_kwargs=cb_kwargs_dict,
                                      headers=self.mobile_user_agent)
            elif 'following' in link:
                yield response.follow(link,
                                      callback=self.following_parse,
                                      cb_kwargs=cb_kwargs_dict,
                                      headers=self.mobile_user_agent)

    def followers_parse(self, response: HtmlResponse, username, user_id, variables):
        j_data = response.json()
        if j_data.get('big_list'):
            variables['max_id'] = j_data.get('next_max_id')
            url_followers = f'https://i.instagram.com/api/v1/friendships/{user_id}/followers/?{urlencode(variables)}&search_surface=follow_list_page'
            yield response.follow(url_followers,
                                  callback=self.followers_parse,
                                  cb_kwargs={'username': username, 'user_id': user_id, 'variables': deepcopy(variables)},
                                  headers=self.mobile_user_agent)
        users = j_data.get('users')
        for user in users:
            item = InstagramItem(user_parser_name=username,
                                 user_id=user.get('pk'),
                                 username=user.get('username'),
                                 photo=user.get('profile_pic_url'),
                                 user_type='follower')
            yield item

    def following_parse(self, response: HtmlResponse, username, user_id, variables):
        j_data = response.json()
        if j_data.get('big_list'):
            variables['max_id'] = j_data.get('next_max_id')
            url_followers = f'https://i.instagram.com/api/v1/friendships/{user_id}/following/?{urlencode(variables)}'
            yield response.follow(url_followers,
                                  callback=self.following_parse,
                                  cb_kwargs={'username': username, 'user_id': user_id, 'variables': deepcopy(variables)},
                                  headers=self.mobile_user_agent)
        users = j_data.get('users')
        for user in users:
            item = InstagramItem(user_parser_name=username,
                                 user_id=user.get('pk'),
                                 username=user.get('username'),
                                 photo=user.get('profile_pic_url'),
                                 user_type='following')
            yield item