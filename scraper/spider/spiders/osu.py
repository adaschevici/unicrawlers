import os
import re
from time import sleep

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

    STUDENTS_TABLE = "//table[@class='searchBox']//tr"
    EMAIL = "./td[4]/a"
    NAME = "./td[1]//a"
    DEPARTMENT = "./td[2]/text()"
    PHONE = "./td[3]/text()"
    CAMPUS = "./td[last()]/text()"
    NEXT_PAGE = "//a[contains(., 'Next')]/@href"

class CONSTANTS:

    BASE_URL = "https://app.it.okstate.edu/directory/index.php/"

class OsuSpider(StudentSpider):
    name = 'osu'
    start_urls = ['https://app.it.okstate.edu/directory/']

    def __init__(self, *args, **kwargs):
        super(OsuSpider, self).__init__(*args, **kwargs)
        self.filter_campus = kwargs.get('filter_campus', 'AM')
        print kwargs
        dispatcher.connect(self.idle, signals.spider_idle)

    def idle(self, spider):
        self.state['progress_current'] = self.state['progress_total']

    def parse(self, response):
        if self.search_type == 'letters':
            self.search_type = 'letters-simple'
        phrases = self.get_search_phrases()
        self.state['progress_current'] = 0
        self.state['progress_total'] = len(phrases)

        for phrase in phrases:
            return self.get_pre_search_request(response, str(phrase))

    def get_pre_search_request(self, response, phrase):
        return FormRequest(
            url='https://app.it.okstate.edu/directory/index.php/module/Default/action/Index',
            formdata={
                'Submit': 'Name Search',
                'fname': '',
                'lname': phrase,
                'var_campus': self.filter_campus
            },
            callback=self.people
        )

    def people(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default
        sel = Selector(response)
        students = sel.xpath(XPATHS.STUDENTS_TABLE)
        if len(students) > 7:
            students = students[1:len(students)-6]
        else:
            return
        self.state['progress_current'] += 1
        next = sel.xpath(XPATHS.NEXT_PAGE)
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
                yield StudentItem(
                    name=name,
                    email=email,
                    campus=campus,
                    phone=phone,
                    department=department
                )
        if next:
            yield Request(
                url=CONSTANTS.BASE_URL + next.extract()[0],
                callback=self.people
            )
