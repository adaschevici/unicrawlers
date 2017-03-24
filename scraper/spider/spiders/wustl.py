import os
import re

from twisted.internet import reactor, defer
from scrapy.selector import Selector
from spider.items import StudentItem
from scrapy.http import Request
from scrapy.http import FormRequest
from spider.spiders.basic import StudentSpider
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from scrapy.utils.markup import replace_tags

class XPATHS:

    STUDENTS_TABLE = "//div[@class='results']//li/a/@href"
    PERSON_DIV = "//div[@class='results']"
    EMAIL = ".//span[contains(., 'email:')]/following-sibling::span[1]"
    NAME = ".//span[contains(., 'name:')]/following-sibling::span[1]"
    ADDRESS = ".//span[contains(., 'address:')]/following-sibling::span[1]"
    DEPARTMENT = ".//span[contains(., 'department:')]/following-sibling::span[1]"
    PHONE = ".//span[contains(., 'phone:')]/following-sibling::span[1]"


class CONSTANTS:

    BASE_URL = "http://wustl.edu"

class WustlSpider(StudentSpider):
    name = 'wustl'
    start_urls = ['http://wustl.edu/directory/']

    def __init__(self, *args, **kwargs):
        super(WustlSpider, self).__init__(*args, **kwargs)
        dispatcher.connect(self.idle, signals.spider_idle)

    def idle(self, spider):
        self.state['progress_current'] = self.state['progress_total']

    def parse(self, response):
        # if self.search_type == 'letters':
        #     self.search_type = 'letters-two'
        phrases = self.get_search_phrases()
        # from scrapy.shell import inspect_response
        # inspect_response(response)
        self.state['progress_current'] = 0
        self.state['progress_total'] = len(phrases)

        for phrase in phrases:
            yield self.get_search_request(response, str(phrase))

    def get_search_request(self, response, phrase):
        return FormRequest(
            url='http://wustl.edu/cgi-bin/directory/index-2012.pl',
            formdata={
                'email': '',
                'name': phrase,
                'phone': ''
            },
            callback=self.people
        )

    def people(self, response):
        sel = Selector(response)
        hrefs = sel.xpath(XPATHS.STUDENTS_TABLE).extract()
        for lnk in hrefs:
            yield Request(
                url=CONSTANTS.BASE_URL+lnk,
                callback=self.parse_people
            )

    def parse_people(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default
        sel = Selector(response)
        person = sel.xpath(XPATHS.PERSON_DIV)
        name = replace_tags(lget(person.xpath(XPATHS.NAME).extract(), 0, ''))
        email = replace_tags(lget(person.xpath(XPATHS.EMAIL).extract(), 0, ''))
        department = replace_tags(lget(person.xpath(XPATHS.DEPARTMENT).extract(), 0, ''))
        address = replace_tags(lget(person.xpath(XPATHS.ADDRESS).extract(), 0, ''))
        phone = replace_tags(lget(person.xpath(XPATHS.PHONE).extract(), 0, ''))
        yield StudentItem(
            name=name,
            email=email,
            department=department,
            address=address,
            phone=phone
        )