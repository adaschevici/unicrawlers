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

    STUDENTS_TABLE = "//table[@class='bordertable']//tr"
    EMAIL = "./td[last()]//a/text()"
    NAME = "./td[1]"
    DEPARTMENT = "./td[2]/text()"
    PHONE = "./td[3]/text()"

class CONSTANTS:

    BASE_URL = "https://banweb.uncg.edu"

class OduSpider(StudentSpider):
    name = 'odu'
    start_urls = ['http://www.odu.edu/directory']

    def __init__(self, *args, **kwargs):
        super(OduSpider, self).__init__(*args, **kwargs)
        self.filter_role = kwargs.get('filter_role', 'A')
        dispatcher.connect(self.idle, signals.spider_idle)

    def idle(self, spider):
        self.state['progress_current'] = self.state['progress_total']

    def parse(self, response):
        if self.search_type == 'letters':
            self.search_type = 'letters-two'
        phrases = self.get_search_phrases()
        # from scrapy.shell import inspect_response
        # inspect_response(response)
        self.state['progress_current'] = 0
        self.state['progress_total'] = len(phrases)

        for phrase in phrases:
            yield self.get_search_request(response, str(phrase))

    def get_search_request(self, response, phrase):
        return Request(
            url="http://www.odu.edu/directory?F_NAME=&L_NAME=%s&SEARCH_IND=%s" % (phrase, self.filter_role),
            callback=self.people
        )

    def people(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default
        sel = Selector(response)
        people_tbl = sel.xpath(XPATHS.STUDENTS_TABLE)
        for person in people_tbl:
            name = replace_tags(lget(person.xpath(XPATHS.NAME).extract(), 0, ''))
            email = lget(person.xpath(XPATHS.EMAIL).extract(), 0, '')
            dept = replace_tags(lget(person.xpath(XPATHS.DEPARTMENT).extract(), 0, ''))
            phone = replace_tags(lget(person.xpath(XPATHS.PHONE).extract(), 0, ''))
            yield StudentItem(
                name=name,
                department=dept,
                email=email,
                phone=phone
            )