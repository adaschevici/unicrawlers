# -*- coding: utf-8 -*- 
import os
import re
import json

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

class UarkSpider(StudentSpider):
    name = 'uark'
    start_urls = ['http://directory.uark.edu/']

    def __init__(self, *args, **kwargs):
        super(UarkSpider, self).__init__(*args, **kwargs)
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
            url='http://campusdata.uark.edu/apiv2/people?$filter=(PreferredClassification+eq+%%27Student%%27+and+LastName+eq+%%27%s%%27)&callback=searchPeople' % (phrase,),
            callback=self.people
        )

    def people(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default

        self.state['progress_current'] += 1
        json_data = response.body[13:-1]
        students = json.loads(json_data)
        
        for student in students:
            name = student['DisplayName']
            email = student['Email']
            level = student['Level']

            yield StudentItem(
                name=name,
                email=email,
                level=level
            )
