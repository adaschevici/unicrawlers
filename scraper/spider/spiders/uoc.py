# -*- coding: utf-8 -*- 
import os

from twisted.internet import reactor, defer
from scrapy.selector import Selector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.spider import BaseSpider
from scrapy.http import Request
from scrapy import log
from urllib import urlencode
from spider.items import StudentItem
from scrapy.http import FormRequest
from spider.spiders.basic import StudentSpider
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals

class UocSpider(StudentSpider):
    name = 'uoc'
    start_urls = ['https://ucdirectory.uc.edu/StudentSearch.asp']

    def __init__(self, *args, **kwargs):
        super(UocSpider, self).__init__(*args, **kwargs)
        dispatcher.connect(self.idle, signals.spider_idle)

    def idle(self, spider):
        if spider != self:
            return

        request = self.process_queue()

        if request:
            self.crawler.engine.crawl(request, spider=self)
        else:
            self.state['progress_current'] = self.state['progress_total']

    def parse(self, response):
        phrases = self.get_search_phrases()

        from scrapy.shell import inspect_response
        inspect_response(response)

        self.state['progress_current'] = 0
        self.state['progress_total'] = len(phrases)

        for phrase in phrases:
            yield self.get_search_request(response, str(phrase))

    def get_search_request(self, response, phrase):
        return FormRequest(
            url='https://ucdirectory.uc.edu/StudentSearch.asp',
            formdata={
                'formLastname': phrase,
                'formFirstname': '',
                'formMode': 'S',
                'formSoundsLike': ''
            },
            callback=self.people
        )

    def people(self, response):
        sel = Selector(response)
        students = sel.xpath('//*[@id="table1"]/tbody/tr[2]/td[1]/font')

        from scrapy.shell import inspect_response
        inspect_response(response)

        self.state['progress_current'] += 1
        
        for student in students:
            print student
