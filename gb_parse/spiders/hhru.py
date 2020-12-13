import scrapy
import re
from ..loaders import HhruLoader


class HhruSpider(scrapy.Spider):
    name = 'hhru'
    db_type = 'MONGO'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']

    main_xpath = {
        'pagination': '//div[@data-qa="pager-block"]//a[@data-qa="pager-page"]/@href',
        'vacancy_url': '//a[@data-qa="vacancy-serp__vacancy-title"]/@href',
    }

    vacancy_xpath = {
        "title": '//h1[@data-qa="vacancy-title"]/text()',
        "salary": '//p[@class="vacancy-salary"]//text()',
        "description": '//div[@data-qa="vacancy-description"]//text()',
        "skills": '//div[@class="bloko-tag-list"]//span[@data-qa="bloko-tag__text"]/text()',
        "vacancy_author_url": "//a[@data-qa='vacancy-company-name']/@href",
    }

    company_xpath = {
        # 'company_name': "//h1/span[contains(@class, 'company-header-title-name')]//text()",
        'company_name': "//meta[@property='og:title']/@content",
        'company_website': "//a[contains(@data-qa, 'company-site')]/@href",
        'company_description': "//div[contains(@data-qa, 'company-description')]//text()",
        "company_tags": "//div[@class='employer-sidebar-block']/p/text()",
    }


    def parse(self, response, **kwargs):
        for pag_page in response.xpath(self.main_xpath['pagination']):
            yield response.follow(pag_page, callback=self.parse)

        for vacancy_page in response.xpath(self.main_xpath['vacancy_url']):
            yield response.follow(vacancy_page, callback=self.vacancy_parse)

    def vacancy_parse(self, response, **kwargs):
        loader = HhruLoader(response=response)
        loader.add_value('url', response.url)
        for name, selector in self.vacancy_xpath.items():
            loader.add_xpath(name, selector)

        # yield loader.load_item()
        yield response.follow(response.xpath(self.vacancy_xpath['vacancy_author_url']).get(),
                              callback=self.company_parse,
                              meta={'item': loader.load_item()})

    def company_parse(self, response, **kwargs):
        nested_loader = HhruLoader(item=response.meta['item'], response=response)
        for name, selector in self.company_xpath.items():
            nested_loader.add_xpath(name, selector)

        yield nested_loader.load_item()

        company_vacancies_url = self.get_company_vacancies(response)
        yield response.follow(url=company_vacancies_url, callback=self.parse)

    def get_company_vacancies(self, response, **kwargs):
        employee_hh_url = str(response.xpath("//link[@rel='canonical']/@href").get())
        employee_id = re.search(r'employer/([0-9]*)', employee_hh_url).group(1)
        return f'https://hh.ru/search/vacancy?st=searchVacancy&from=employerPage&employer_id={employee_id}' if employee_id else None

        # if 1:
        #     yield {}
        # else:
        #     yield from self.company_parse_B(response, item=item)

    # def company_parse_B(self, response, **kwargs):
    #     if 1:
    #         yield {}
    #     else:
    #         for r in self.company_parse_C(response):
    #             yield r




