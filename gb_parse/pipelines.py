# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


from itemadapter import ItemAdapter
from pymongo import MongoClient
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline


class GbParsePipeline:
    def __init__(self):
        # self.db = MongoClient()['parse_gb_hhru']
        # self.db = MongoClient()['parse_gb_insta']
        self.db = MongoClient()['parse_gb_follower']

    def process_item(self, item, spider):
        if spider.db_type == 'MONGO':
            collection = self.db[spider.name]
            collection.insert_one(item)
        return item


class GbImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        for url in item.get('image_urls', []):
            try:
                yield Request(url)
            except Exception as e:
                print(e)

    def item_completed(self, results, item, info):
        if item.get('image_urls'):
            item['image_urls'] = [itm[1] for itm in results if itm[0]]
        return item
