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

class ColoradoSpider(StudentSpider):
    name = 'colorado'
    start_urls = ['http://www.colorado.edu/gsearch/students']

    def __init__(self, *args, **kwargs):
        super(ColoradoSpider, self).__init__(*args, **kwargs)
        dispatcher.connect(self.idle, signals.spider_idle)

    def idle(self, spider):
        self.state['progress_current'] = self.state['progress_total']

    def parse(self, response):
        phrases = self.get_search_phrases()

        self.state['progress_current'] = 0
        self.state['progress_total'] = len(phrases)

        for phrase in phrases:
            yield self.get_search_request(response, str(phrase))

    def get_search_request(self, response, phrase):
        return Request(
            url='http://www.colorado.edu/gsearch/students/%s' % (phrase,),
            callback=self.people
        )

    def people(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default

        self.state['progress_current'] += 1

        sel = Selector(response)
        students = sel.xpath('//*[@class="cu-directory-results"]/li')

        for student in students:
            name = student.xpath('.//strong/a/text()').extract()[0]
            meta = student.xpath('.//div[@class="people-meta"]')
            major = lget(meta.xpath('.//div[@class="people-major"]/text()').extract(), 0, '')[2:]
            department = lget(meta.xpath('.//div[@class="people-department"]/text()').extract(), 0, '')[2:]
            email = lget(meta.xpath('.//div[@class="people-data"]/a[@class="email-long"]/text()').extract(), 0, '').lower()
            phone = lget(meta.xpath('.//div[@class="people-data"]/text()').extract(), 1, '')[3:]
            address = meta.xpath('.//div[@class="people-address"]/text()').extract()
            
            if address and len(address) == 2:
                address = '%s (box: %s)' % (address[1].strip(), address[0].strip()[2:],)
            else:
                address = ''

            yield StudentItem(
                name=name,
                email=email,
                major1=major,
                phone=phone,
                department=department,
                address=address
            )
