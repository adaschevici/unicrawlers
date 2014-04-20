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

class XPATHS:

    STUDENT_SECTION = "//div[@id='biodemo']"
    NAME = "./h2/text()"
    DEGREE = "./p[%s]/text()"
    EMAIL = "./p/a/text()"

class UindySpider(StudentSpider):
    name = 'uindy'
    start_urls = ['http://www.uindy.edu/search/people?']

    def idle(self, spider):
        self.state['progress_current'] = self.state['progress_total']

    def __init__(self, *args, **kwargs):
        super(UindySpider, self).__init__(*args, **kwargs)
        dispatcher.connect(self.idle, signals.spider_idle)


    def parse(self, response):
        phrases = self.get_search_phrases()

        self.state['progress_current'] = 0
        self.state['progress_total'] = len(phrases)
        for phrase in phrases:
            yield self.get_search_request(response, str(phrase))

    def get_search_request(self, response, phrase):
        return Request(
            url='http://www.uindy.edu/search/people?h=%s' % (phrase,),
            callback=self.people
        )

    def people(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default

        self.state['progress_current'] += 1
        sel = Selector(response)
        students = sel.xpath(XPATHS.STUDENT_SECTION)
        for student in students:
            name = student.xpath(XPATHS.NAME)[0].extract()
            part1 = student.xpath(XPATHS.DEGREE % 1)[0].extract()
            part2 = student.xpath(XPATHS.DEGREE % 2)[0].extract()
            degree = part1 + part2
            degree = ' '.join(degree)
            email = student.xpath(XPATHS.EMAIL)[0].extract()
            yield StudentItem(
                name=name,
                email=email,
                department=degree
            )