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

    STUDENTS_TABLE = "//table[@class='phone_list']//tr"
    EMAIL = "./td[2]/p/a/text()"
    NAME = "./td[1]/p/a/text()"
    PHONE = "./td[3]/p/text()"
    GROUP = "./td[last()]/p/text()"

class CONSTANTS:

    BASE_URL = "https://banweb.uncg.edu"

class TulaneSpider(StudentSpider):
    name = 'tulane'
    start_urls = ['http://tulane.edu/phonebook.cfm']

    def __init__(self, *args, **kwargs):
        super(TulaneSpider, self).__init__(*args, **kwargs)
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
            url='http://tulane.edu/phonebook.cfm',
            formdata={
                'S': '',
                'Search': 'Search',
                'name': phrase
            },
            callback=self.people
        )

    def people(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default
        self.state['progress_current'] += 1
        sel = Selector(response)
        people_rows = sel.xpath(XPATHS.STUDENTS_TABLE)
        self.log('<<<<<<<<<<<<<<<<%s<<<<<<<<<<<<' % len(people_rows))
        for person in people_rows:
            name = replace_tags(lget(person.xpath(XPATHS.NAME).extract(), 0, ''))
            email = replace_tags(lget(person.xpath(XPATHS.EMAIL).extract(), 0, ''))
            phone = replace_tags(lget(person.xpath(XPATHS.PHONE).extract(), 0, ''))
            department = replace_tags(lget(person.xpath(XPATHS.GROUP).extract(), 0, ''))
            pos_com = department.find(',')
            status = department[:pos_com]
            act_department = department[pos_com+1:]
            yield StudentItem(
                name=name,
                email=email,
                phone=phone,
                level=status,
                department=act_department
            )