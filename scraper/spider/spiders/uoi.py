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

class UoiSpider(StudentSpider):
    name = 'uoi'
    start_urls = ['http://dnaapps.uiowa.edu/PublicDirectory/Default.aspx']

    def __init__(self, *args, **kwargs):
        super(UoiSpider, self).__init__(*args, **kwargs)
        self.filter_type = kwargs.get('filter_type', 2)
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
        return FormRequest.from_response(response,
            formdata={
                'ctl00$ContentPlaceHolder1$SimpleSearchNameTextBox': phrase
            },
            formname='aspnetForm',
            callback=self.people
        )

    def people(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default

        self.state['progress_current'] += 1

        sel = Selector(response)
        students = sel.xpath('//table/tr[@class="table_row_odd" or @class="table_row_even"]')

        for student in students:
            cols = student.xpath('.//td/a/text()').extract()
            name = lget(cols, 0, '')
            email = lget(cols, 1, '')
            phone = lget(cols, 2, '')
            department = lget(student.xpath('.//td[4]/text()').extract(), 0, '')

            yield StudentItem(
                name=name,
                email=email,
                phone=phone,
                department=department
            )
