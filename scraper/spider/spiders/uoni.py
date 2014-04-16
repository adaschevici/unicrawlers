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

class UoniSpider(StudentSpider):
    name = 'uoni'
    start_urls = ['https://java.access.uni.edu/ed/faces/searchStudent.jsp']

    def __init__(self, *args, **kwargs):
        super(UoniSpider, self).__init__(*args, **kwargs)
        dispatcher.connect(self.idle, signals.spider_idle)

    def parse(self, response):
        if self.search_type == 'letters':
            self.search_type = 'letters-simple'

        self.state['phrases'] = self.get_search_phrases()
        self.state['progress_current'] = 0
        self.state['progress_total'] = len(self.state['phrases'])
        self.state['page_queue'] = []

        return self.process_queue()

    def idle(self, spider):
        if spider != self:
            return

        request = self.process_queue()

        if request:
            self.crawler.engine.crawl(request, spider=self)
        else:
            self.state['progress_current'] = self.state['progress_total']

    def process_queue(self, response=None):
        if self.state['page_queue']:
            return self.state['page_queue'].pop()
        if self.state['phrases']:
            if not response:
                return Request(url=UoniSpider.start_urls[0], callback=self.process_queue, dont_filter = True)
            else:
                self.state['progress_current'] += 1
                phrase = self.state['phrases'].pop()
                return self.get_search_request(response, str(phrase))

    def get_search_request(self, response, phrase):
        return FormRequest.from_response(response,
            formdata={
                'form1:txtLastName': phrase,
                'form1:txtFirstName': '',
                'form1:txtEmail': '',
                'form1:soMajor': '0',
                'form1:soCollege': '0',
                'form1:soClass': '0', # todo: configurable
                'event': '',
                'value': 'all',
                'partial': '',
                'source': 'form1:cmdSearch1'
            },
            dont_click=False,
            callback=self.get_all,
            formname='form1'
        )

    def get_all(self, response):
        return self.get_page(response, 0)

    def get_page(self, response, offset):
        return FormRequest.from_response(response,
            formdata={
                'form1:table1:rangeStart': str(offset),
                'event': 'goto',
                'value': str(offset + 1),
                'partial': 'true',
                'source': 'form1:table1'
            },
            dont_click=False,
            callback=self.people,
            formname='form1',
            meta={'offset': offset}
        )

    def get_student_details_request(self, response, index):
        return FormRequest.from_response(response,
            formdata={
                'form1:table1:rangeStart': '0',
                'event': '',
                'partial': '',
                'value': 'all',
                'source': 'form1:table1:%d:cmdMoreInfo' % index
            },
            dont_click=False,
            callback=self.student_info,
            formname='form1'
        )

    def people(self, response):
        sel = Selector(response)
        students = sel.xpath('//*[@id="form1:table1"]/table[2]//tr')

        self.state['progress_total'] += len(students)

        for i, student in enumerate(students[1:]):
            yield self.get_student_details_request(response, i)

        next_page = sel.xpath('//*[@id="form1:table1-nb"]/tr/td[7]/a')

        print "NEXT_PAGE: "
        print next_page
        #from scrapy.shell import inspect_response
        #inspect_response(response)

        if next_page:
            self.state['page_queue'].append(self.get_page(response, response.meta['offset'] + 20))
    
    def student_info(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default

        self.state['progress_current'] += 1

        sel = Selector(response)
        email = lget(sel.xpath('//*[@id="form1:goLink6"]/text()').extract(), 0, '')
        name = sel.xpath('//*[@id="form1:outputText2"]/text()').extract()[0]
        address = lget(sel.xpath('//*[@id="form1:outputText23"]/text()').extract(), 0, '')
        city = lget(sel.xpath('//*[@id="form1:outputText25"]/text()').extract(), 0, '')
        major = lget(sel.xpath('//*[@id="form1:outputText17"]/text()').extract(), 0, '')
        college = lget(sel.xpath('//*[@id="form1:outputText20"]/text()').extract(), 0, '')
        _class = lget(sel.xpath('//*[@id="form1:outputText16"]/text()').extract(), 0, '')
        
        return StudentItem(
            name=name,
            email=email,
            address=address,
            city=city,
            major1=major,
            college=college,
            _class=_class
        )
