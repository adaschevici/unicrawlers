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

class MnsuSpider(StudentSpider):
    name = 'mnsu'
    start_urls = ['http://www.mnsu.edu/find/people.php?givenname=&sn=&employeetype=student']

    def __init__(self, *args, **kwargs):
        super(MnsuSpider, self).__init__(*args, **kwargs)
        self.filter_role = kwargs.get('filter_role', 'A')
        print kwargs
        print '*' * 10, self.filter_role, '*' * 10
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
            url='http://www.mnsu.edu/find/people.php?givenname=%s&%s=han&employeetype=%s' % (),
            callback=self.people
        )

    def people(self, response):
        sel = Selector(response)

