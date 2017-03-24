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

class CONSTANTS:

    BASE_URL = "https://www.directory.gatech.edu"

class XPATHS:

    STUDENT_LINKS = "//div[@id='block-system-main']/div/p/a/@href"
    STUDENT_SECTION = "//div[@id='block-system-main']"
    NAME = ".//h2/text()"
    DEPT = ".//p[contains(., 'DEPARTMENT')]/text()"
    EMAIL = ".//p[contains(., 'E-MAIL')]/a/text()"
    TITLE = ".//p[contains(., 'TITLE')]/text()"
    PO = ".//p[contains(., 'DEPT. MAIL CODE')]/text()"

class GatechSpider(StudentSpider):
    name = 'gatech'
    start_urls = ['https://www.directory.gatech.edu/']

    def idle(self, spider):
        self.state['progress_current'] = self.state['progress_total']

    def __init__(self, *args, **kwargs):
        super(GatechSpider, self).__init__(*args, **kwargs)
        dispatcher.connect(self.idle, signals.spider_idle)

    def parse(self, response):
        phrases = self.get_search_phrases()

        self.state['progress_current'] = 0
        self.state['progress_total'] = len(phrases)
        for phrase in phrases:
            yield self.get_search_request(response, str(phrase))

    def get_search_request(self, response, phrase):
        return Request(
            url='https://www.directory.gatech.edu/directory/results//%s' % (phrase,),
            callback=self.people
        )

    def people(self, response):
        self.state['progress_current'] += 1
        sel = Selector(response)
        student_links = sel.xpath(XPATHS.STUDENT_LINKS)
        for link in student_links:
            self.log(CONSTANTS.BASE_URL+link.extract())
            yield Request(url=CONSTANTS.BASE_URL+link.extract(),
                          callback=self.extract_students
                          )

    def extract_students(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default

        sel = Selector(response)
        atributes = sel.xpath(XPATHS.STUDENT_SECTION)
        for att in atributes:
            name = lget(att.xpath(XPATHS.NAME).extract(), 0, '')
            email = lget(att.xpath(XPATHS.EMAIL).extract(), 0, '')
            dept = lget(att.xpath(XPATHS.DEPT).extract(), 0, '')
            title = lget(att.xpath(XPATHS.TITLE).extract(), 0, '')
            pobox = lget(att.xpath(XPATHS.PO).extract(), 0, '')
            yield StudentItem(
                name=name,
                email=email,
                department=dept,
                address=pobox,
                degree=title
            )

