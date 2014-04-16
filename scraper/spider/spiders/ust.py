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

class UstSpider(StudentSpider):
    name = 'ust'
    start_urls = ['http://www.stthomas.edu/directories/']

    def __init__(self, *args, **kwargs):
        super(UstSpider, self).__init__(*args, **kwargs)
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
        return Request(
            url='http://webapp.stthomas.edu/directory/personsearchresults.htm?searchtype=Last+Name&searchtext=%s' % (phrase,),
            callback=self.people
        )

    def people(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default


        sel = Selector(response)
        students = sel.xpath('//table/tr/td/a/@href').extract()

        self.state['progress_current'] += 1
        self.state['progress_total'] += len(students)

        for url in students:
            yield Request(url='http://webapp.stthomas.edu/directory/' + url, callback=self.people_details)

    def people_details(self, response):
        self.state['progress_current'] += 1
        
        sel = Selector(response)
        name = sel.xpath('//*[@id="directory"]/div/h3/text()').extract()[0].strip()
        fields = sel.xpath('//table/tr')
        data = {}

        for field in fields:
            key = field.xpath('.//td[1]/text()').extract()[0].strip()
            value = field.xpath('.//td[2]')

            if 'Email' in key:
                value = value.xpath('.//a/text()')
            else:
                value = value.xpath('.//text()')

            data[key] = value.extract()[0].strip()

        print data

        yield StudentItem(
            name=name,
            email=data.get('Email :', data.get('Email', '')),
            address=data.get('Location :', data.get('Location', '')),
            phone=data.get('Phone :', data.get('Phone', '')),
            department=data.get('Department Assignment :', data.get('Department Assignment', '')),
        )
