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

    STUDENTS_TABLE = "//table[@id='AutoNumber8']//tr//tr"
    EMAIL = "./td[3]//a/text()"
    NAME = "./td[2]/a/text()"
    DEPARTMENT = "./td[5]/text()"
    PHONE = "./td[4]/text()"
    STATUS = "./td[6]/text()"
    CAMPUS = "./td[7]/text()"
    ADDRESS = "./td[8]/text()"

class CONSTANTS:

    BASE_URL = "https://banweb.uncg.edu"

class SiucSpider(StudentSpider):
    name = 'siuc'
    start_urls = ['https://itmfs1.it.siu.edu/php/index.php']

    def __init__(self, *args, **kwargs):
        super(SiucSpider, self).__init__(*args, **kwargs)
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
        self.state['progress_current'] = 0
        self.state['progress_total'] = len(phrases)

        for phrase in phrases:
            yield self.get_search_request(response, str(phrase))

    def get_search_request(self, response, phrase):
        return FormRequest(
            url='https://itmfs1.it.siu.edu/php/index_fmt.php',
            formdata={
                'SCriteria': 'sn',
                'SType': 'starts with',
                'Search': 'Search',
                'SearchFor': self.filter_role,
                'TextSearch': phrase
            },
            callback=self.people
        )

    def people(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default
        sel = Selector(response)
        students = sel.xpath(XPATHS.STUDENTS_TABLE)
        for student in students:
            name = replace_tags(lget(student.xpath(XPATHS.NAME).extract(), 0, ''))
            name = Sanitizer.trim(name)
            email = replace_tags(lget(student.xpath(XPATHS.EMAIL).extract(), 0, ''))
            email = Sanitizer.trim(email)
            department = replace_tags(lget(student.xpath(XPATHS.DEPARTMENT).extract(), 0, ''))
            department = Sanitizer.trim(department)
            phone = replace_tags(lget(student.xpath(XPATHS.PHONE).extract(), 0, ''))
            phone = Sanitizer.trim(phone)
            campus = replace_tags(lget(student.xpath(XPATHS.CAMPUS).extract(), 0, ''))
            campus = Sanitizer.trim(campus)
            degree = replace_tags(lget(student.xpath(XPATHS.STATUS).extract(), 0, ''))
            degree = Sanitizer.trim(degree)
            yield StudentItem(
                    name=name,
                    email=email,
                    campus=campus,
                    phone=phone,
                    department=department,
                    degree=degree
            )
