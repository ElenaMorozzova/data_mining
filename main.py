from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
# from gb_parse.spiders.autoyoula import AutoyoulaSpider
from gb_parse.spiders.hhru import HhruSpider
from gb_parse.spiders.instagram import InstagramSpider
from gb_parse.spiders.insta_handshakes import HandshakesSpider

import dotenv
import os
dotenv.load_dotenv('.env')

if __name__ == '__main__':
    crawl_settings = Settings()
    crawl_settings.setmodule('gb_parse.settings')
    crawl_proc = CrawlerProcess(settings=crawl_settings)
    # crawl_proc.crawl(HhruSpider)
    # crawl_proc.crawl(InstagramSpider, login=os.getenv('LOGIN'), password=os.getenv('PASSWORD'), user_list=['sevcableport', ], tag_list=['python', ])
    crawl_proc.crawl(HandshakesSpider, login=os.getenv('LOGIN'), password=os.getenv('PASSWORD'))
    crawl_proc.start()
