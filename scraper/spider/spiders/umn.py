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

class UmnSpider(StudentSpider):
    name = 'umn'
    start_urls = ['http://www.umn.edu/']

    def __init__(self, *args, **kwargs):
        super(UmnSpider, self).__init__(*args, **kwargs)
        self.filter_role = kwargs.get('filter_role', 'any')
        self.filter_campus = kwargs.get('filter_campus', 'a')
        dispatcher.connect(self.idle, signals.spider_idle)

    def idle(self, spider):
        self.state['progress_current'] = self.state['progress_total']

    def parse(self, response):
        if self.search_type == 'file':
            self.search_type = 'file-letter'

        phrases = self.get_search_phrases()

        self.state['progress_current'] = 0
        self.state['progress_total'] = len(phrases)

        for phrase in phrases:
            yield self.get_search_request(response, str(phrase))

    def get_search_request(self, response, phrase):
        return Request(
            url='http://www.umn.edu/lookup?SET_INSTITUTION=UMNTC&type=name&CN=%s&campus=%s&role=%s' % (phrase, self.filter_campus, self.filter_role,),
            callback=self.people
        )

    def people(self, response):
        self.state['progress_current'] += 1

        sel = Selector(response)
        students = sel.xpath('//*[@id="pagecontent"]/table/tr')[1:]

        self.state['progress_total'] += len(students)

        try:
            for student in students:
                details = 'http://www.umn.edu' + student.xpath('.//td[1]/a/@href').extract()[0]
                department = student.xpath('.//td[5]/text()').extract()[0]

                yield Request(url=details, meta={'department': department}, callback=self.details)
        except:
            yield self.details(response)

    def details(self, response):
        department = response.meta.get('department', '')
        sel = Selector(response)
        name = sel.xpath('//*[@id="pagecontent"]/h2/text()').extract()[0]

        data = {}
        fields = sel.xpath('//*[@id="pagecontent"]/table/tr')

        self.state['progress_current'] += 1

        for field in fields:
            key = field.xpath('.//th/text()').extract()[0]
            value = field.xpath('.//td')
            
            if 'Enrollment' in key:
                data['enrollment'] = ', '.join([x.strip() for x in value.xpath('.//text()').extract()])
            elif 'Email' in key:
                data['email'] = value.xpath('.//a//text()').extract()[0]
            elif 'Phone' in key:
                data['phone'] = value.xpath('.//text()').extract()[0].strip()
            elif 'Address' in key:
                data['address'] = ', '.join([x.strip() for x in value.xpath('.//text()').extract()])

        yield StudentItem(
            name=name,
            department=department,
            enrollment=data.get('enrollment', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            address=data.get('address', '')
        )



