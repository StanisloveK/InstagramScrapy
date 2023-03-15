# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient
import pymongo


class InstagramPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongobase = client.instagram

    def process_item(self, item, spider):
        collection = self.mongobase[item['user_parser_name']]
        collection.create_index([('user_id', pymongo.TEXT)], name='unique description', unique=True)
        del item['user_parser_name']
        collection.insert_one(item)
        return item