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
from spider.utils import Sanitizer

class XPATHS:

    STUDENTS_TABLE = "//table[@class='search-results']//tr//a/@href"
    NEXT_PAGE = "//td/a[./img[@alt='Next' and @src='/ru-directory/images/left-arrow.gif']]/@href"

    PERSON_ROWS = "//div[@id='details']//table//tr"
    NAME = "(//div[@id='details']//table//tr)[1]/td[2]/text()"
    STATUS = "(//div[@id='details']//table//tr)[2]/td[2]/text()"
    EMAIL = "(//div[@id='details']//table//tr)[3]/td[2]/a/text()"

class CONSTANTS:

    BASE_URL = "https://webapps.radford.edu"

class RaduSpider(StudentSpider):
    name = 'radu'
    start_urls = ['https://webapps.radford.edu/ru-directory/content/search/partialLastName']

    def __init__(self, *args, **kwargs):
        super(RaduSpider, self).__init__(*args, **kwargs)
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
        return FormRequest(
            url='https://webapps.radford.edu/ru-directory/content/results/partialLastName',
            formdata={
                'pln': phrase
            },
            callback=self.people
        )

    def people(self, response):
        sel = Selector(response)
        student_links = sel.xpath(XPATHS.STUDENTS_TABLE)
        next = sel.xpath(XPATHS.NEXT_PAGE)
        print 10*'*', len(student_links), 10*'*'
        for lnk in student_links:
            print lnk.extract()[0]
            yield Request(
                url=CONSTANTS.BASE_URL + lnk.extract(),
                callback=self.parse_person
            )
        if next:
            yield Request(
                url=CONSTANTS.BASE_URL + next.extract(),
                callback=self.people
            )
    def parse_person(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default
        sel = Selector(response)
        rows = sel.xpath(XPATHS.PERSON_ROWS)
        name = replace_tags(lget(sel.xpath(XPATHS.NAME).extract(), 0, ''))
        name = Sanitizer.trim(name)
        email = replace_tags(lget(sel.xpath(XPATHS.EMAIL).extract(), 0, ''))
        email = Sanitizer.trim(email)
        degree = replace_tags(lget(sel.xpath(XPATHS.STATUS).extract(), 0, ''))
        degree = Sanitizer.trim(degree)
        yield StudentItem(
                name=name,
                email=email,
                degree=degree
        )

