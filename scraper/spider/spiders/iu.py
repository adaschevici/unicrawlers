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


    HIDDEN_SID = "//input[@name='sid']/@value"

    STUDENTS_TABLE = "//div[@class='large-8 columns end']//tr"

    STUDENT_LINK = "./td[1]/a/@href"

    NAME = "//th[@class='details']//font/text()"

    CAMPUS = "(//div[@class='large-8 columns end']//tr/td[1]/following-sibling::td)[1]"

    DEPARTMENT = "(//div[@class='large-8 columns end']//tr/td[1]/following-sibling::td)[3]"

    ADDRESS = "(//div[@class='large-8 columns end']//tr/td[1]/following-sibling::td)[4]"

    EMAIL = "(//div[@class='large-8 columns end']//tr/td[1]/following-sibling::td)[5]"

class CONSTANTS:

    BASE_URL = "http://people.iu.edu/"

class IuSpider(StudentSpider):
    name = 'iu'
    start_urls = ['http://people.iu.edu/']

    def __init__(self, *args, **kwargs):
        super(IuSpider, self).__init__(*args, **kwargs)
        self.filter_role = kwargs.get('filter_role', 'Any')
        self.filter_campus = kwargs.get('filter_campus', 'Any')
        print kwargs
        print '*' * 10, self.filter_role, '*' * 10
        dispatcher.connect(self.idle, signals.spider_idle)
        self.debug = False

    def idle(self, spider):
        self.state['progress_current'] = self.state['progress_total']

    def parse(self, response):
        if self.search_type == 'file':
            self.search_type = 'file-letter'
        sel = Selector(response)
        self.sid = sel.xpath(XPATHS.HIDDEN_SID).extract()[0]
        phrases = self.get_search_phrases()
        self.state['progress_current'] = 0
        self.state['progress_total'] = len(phrases)
        for phrase in phrases:
            return self.get_search_request(response, phrase)

    def get_search_request(self, response, phrase):
        self.log(phrase)
        return FormRequest(
            url='http://people.iu.edu/',
            formdata={
                'lastname': phrase[1],
                'exactness': 'exact',
                'firstname': phrase[0],
                'status': self.filter_role,
                'campus': self.filter_campus,
                'netid': '',
                'Search': 'Search',
                'sid': self.sid

            },
            callback=self.people
        )

    def people(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default
        sel = Selector(response)
        print response.status_code
        # from scrapy.utils.response import open_in_browser
        # open_in_browser(response)
        # if self.debug:
        #     from scrapy.shell import inspect_response
        #     inspect_response(response)
        rows = sel.xpath(XPATHS.STUDENTS_TABLE)
        for student in rows[1:]:
            lnk_part = student.xpath(XPATHS.STUDENT_LINK).extract()[0]
            self.log(lnk_part)
            if lnk_part != '':
                return Request(
                    url=CONSTANTS.BASE_URL + lnk_part,
                    callback=self.parse_people
                )

    def parse_people(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default
        from scrapy.shell import inspect_response
        inspect_response(response)
        sel = Selector(response)
        name = replace_tags(lget(sel.xpath(XPATHS.NAME).extract(), 0, ''))
        name = Sanitizer.trim(name)
        email = replace_tags(lget(sel.xpath(XPATHS.EMAIL).extract(), 0, ''))
        email = Sanitizer.trim(email)
        department = replace_tags(lget(sel.xpath(XPATHS.DEPARTMENT).extract(), 0, ''))
        department = Sanitizer.trim(department)
        address = replace_tags(lget(sel.xpath(XPATHS.ADDRESS).extract(), 0, ''))
        address = Sanitizer.trim(address)
        campus = replace_tags(lget(sel.xpath(XPATHS.CAMPUS).extract(), 0, ''))
        campus = Sanitizer.trim(campus)
        # if name == 'N/A':
        #     from scrapy.utils.response import open_in_browser
        #     open_in_browser(response)

        yield StudentItem(
            name=name,
            campus=campus,
            address=address,
            email=email,
            department=department
        )