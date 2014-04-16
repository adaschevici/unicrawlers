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

class UkySpider(StudentSpider):
    name = 'uky'
    start_urls = ['http://www.uky.edu/Directory/']

    def __init__(self, *args, **kwargs):
        super(UkySpider, self).__init__(*args, **kwargs)
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
            url='http://ukcc.uky.edu/cgi-bin/phq?def=uk&brief=3&field=name&value=%s&x=19&y=9' % (phrase,),
            callback=self.people
        )

    def people(self, response):
        sel = Selector(response)
        students = sel.xpath('//*[@id="main"]/table/tr/td[1]/a/@href').extract()

        self.state['progress_current'] += 1

        for url in students:
            self.state['progress_total'] += len(students)
            yield Request(url=url, callback=self.people)

        if not students:
            self.state['progress_current'] += 1

            students = sel.xpath('//*[@id="main"]/table')

            for student in students:
                data = {}
                fields = student.xpath('.//tr')

                for field in fields:
                    key = field.xpath('.//i/text()').extract()[0]
                    value = field.xpath('.//td[4]')

                    if key in ['Email', 'Address']:
                        value = value.xpath('.//a/text()')
                    else:
                        value = value.xpath('.//text()')

                    data[key] = value.extract()[0]

                yield StudentItem(
                    email=data.get('Email', ''),
                    department=data.get('Department', ''),
                    address=data.get('Address', ''),
                    city=data.get('City', ''),
                    phone=data.get('Phone', ''),
                    name=data.get('Fullname', ''),
                )
