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

    STUDENTS_TABLE = "//table[@summary='Search Results']//tr"
    EMAIL = "./td[last()]//a/text()"
    NAME = "./td[1]"
    ADDRESS = "./td[2]"
    STATUS = "./td[1]//span/text()"
    NEXT_PAGE = "//a[contains(., 'Next Page')]/@href"

class CONSTANTS:

    BASE_URL = "https://banweb.uncg.edu"

class UncgSpider(StudentSpider):
    name = 'uncg'
    start_urls = ['https://banweb.uncg.edu/prod/bwzkwdrs.p_get']

    def __init__(self, *args, **kwargs):
        super(UncgSpider, self).__init__(*args, **kwargs)
        self.filter_role = kwargs.get('filter_role', 'B')
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
            url='https://banweb.uncg.edu/prod/bwzkwdrs.p_search',
            formdata={
                'p_first': '',
                'p_last': phrase,
                'p_pick': self.filter_role
            },
            callback=self.people
        )

    def people(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default
        sel = Selector(response)
        next = sel.xpath(XPATHS.NEXT_PAGE).extract()
        while next:
            people_links = sel.xpath(XPATHS.STUDENTS_TABLE)[1:]
            for person in people_links:
                email = lget(person.xpath(XPATHS.EMAIL).extract(), 0, '')
                name = replace_tags(lget(person.xpath(XPATHS.NAME).extract(), 0, '')).split('--')[0]
                address = replace_tags(lget(person.xpath(XPATHS.ADDRESS).extract(), 0, ''))
                status = lget(person.xpath(XPATHS.STATUS).extract(), 0, '')
                yield StudentItem(
                    name=name,
                    email=email,
                    address=address,
                    degree=status
                )
            yield Request(
                url=CONSTANTS.BASE_URL + next[0],
                callback=self.people
            )
        people_links = sel.xpath(XPATHS.STUDENTS_TABLE)[1:]
        for person in people_links:
                email = lget(person.xpath(XPATHS.EMAIL).extract(), 0, '')
                name = replace_tags(lget(person.xpath(XPATHS.NAME).extract(), 0, '')).split('--')[0]
                address = replace_tags(lget(person.xpath(XPATHS.ADDRESS).extract(), 0, ''))
                status = lget(person.xpath(XPATHS.STATUS).extract(), 0, '')
                yield StudentItem(
                    name=name,
                    email=email,
                    address=address,
                    degree=status
                )