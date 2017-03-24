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

    STUDENTS_TABLE = "//div[@id='markup']//tbody/tr"
    EMAIL = "./td[last()]//a/text()"
    NAME = "./td[1]//a/text()"


class JmuSpider(StudentSpider):
    name = 'jmu'
    start_urls = ['http://www.jmu.edu/cgi-bin/peoplestudentcms']

    def __init__(self, *args, **kwargs):
        super(JmuSpider, self).__init__(*args, **kwargs)
        dispatcher.connect(self.idle, signals.spider_idle)

    def idle(self, spider):
        self.state['progress_current'] = self.state['progress_total']


    def parse(self, response):
        phrases = self.get_search_phrases()

        self.state['progress_current'] = 0
        self.state['progress_total'] = len(phrases)
        for phrase in phrases:
            yield self.get_search_request(response, str(phrase))

    def get_search_request(self, response, phrase):
        return FormRequest(
            url='http://www.jmu.edu/cgi-bin/peoplestudentcms',
            formdata={
                'pattern': phrase
            },
            callback=self.people
        )

    def people(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default
        self.state['progress_current'] += 1
        sel = Selector(response)
        people_table = sel.xpath(XPATHS.STUDENTS_TABLE)
        for person in people_table:
            name = lget(person.xpath(XPATHS.NAME).extract(), 0, '')
            email = lget(person.xpath(XPATHS.EMAIL).extract(), 0, '')
            yield StudentItem(
                name=name,
                email=email
            )


