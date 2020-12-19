import scrapy


class GbParseItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class AutoYoulaItem(scrapy.Item):
    _id = scrapy.Field()
    title = scrapy.Field()
    images = scrapy.Field()
    description = scrapy.Field()
    url = scrapy.Field()
    autor = scrapy.Field()
    specifications = scrapy.Field()


class HhruItem(scrapy.Item):
    _id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    salary = scrapy.Field()
    description = scrapy.Field()
    skills = scrapy.Field()
    vacancy_author_url = scrapy.Field()
    company_name = scrapy.Field()
    company_website = scrapy.Field()
    company_description = scrapy.Field()
    company_tags = scrapy.Field()


class InstaItem(scrapy.Item):
    _id = scrapy.Field()
    date_parse = scrapy.Field()
    data = scrapy.Field()
    image_urls = scrapy.Field()


class InstaTag(InstaItem):
    pass


class InstaPost(InstaItem):
    pass


class InstaUser(InstaItem):
    pass


class InstaFollow(scrapy.Item):
    _id = scrapy.Field()
    date_parse = scrapy.Field()
    user_name = scrapy.Field()
    user_id = scrapy.Field()
    follow_type = scrapy.Field()
    follow_name = scrapy.Field()
    follow_id = scrapy.Field()
