# -*- coding: utf-8 -*- 
import os
import re

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

class UnlSpider(StudentSpider):
    name = 'unl'
    start_urls = ['http://directory.unl.edu/service.php']

    def __init__(self, *args, **kwargs):
        super(UnlSpider, self).__init__(*args, **kwargs)
        self.filter_type = kwargs.get('filter_type', 2)
        dispatcher.connect(self.idle, signals.spider_idle)

    def idle(self, spider):
        self.state['progress_current'] = self.state['progress_total']

    def parse(self, response):
        phrases = self.get_search_phrases()

        self.state['progress_current'] = 0
        self.state['progress_total'] = len(phrases)

        for phrase in phrases:
            yield self.get_search_request(response, str(phrase).strip())

    def get_search_request(self, response, phrase):
        return Request(
            url='http://directory.unl.edu/service.php?q=%s' % phrase,
            callback=self.people
        )

    def people(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default


        sel = Selector(response)
        students = sel.xpath('//*[@id="results_student"]/ul/li/div/div[1]/div[1]/a/@href').extract()

        self.state['progress_current'] += 1
        self.state['progress_total'] += len(students)

        for url in students:
            yield Request(
                url='http:' + url,
                callback=self.people_details
            )

    def people_details(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default

        self.state['progress_current'] += 1

        sel = Selector(response)
        name = sel.xpath('//div[@class="vcardInfo"]//span/text()').extract()[0]
        email = lget(sel.xpath('//a[@class="email"]/text()').extract(), 0, '')

        if email:
            yield StudentItem(
                name=name,
                email=email
            )
