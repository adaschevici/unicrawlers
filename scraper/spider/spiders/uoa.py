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

class UoaSpider(StudentSpider):
    name = 'uoa'
    start_urls = ['http://www.arizona.edu/phonebook/']

    def __init__(self, *args, **kwargs):
        super(UoaSpider, self).__init__(*args, **kwargs)
        self.filter_type = kwargs.get('filter_type', 2)
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
            url='http://www.arizona.edu/phonebook/%s?fac_staff_stud=%d' % (phrase, self.filter_type,),
            callback=self.people
        )

    def people(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default

        self.state['progress_current'] += 1

        sel = Selector(response)
        students = sel.xpath('//*[@id="content-content"]/dl/dt')

        p = re.compile('<dt.*?>.*?\((.*?)\).*?<dd>.*?mailto:(.+?)">(.+?)</p>', flags=re.DOTALL)
        students = p.findall(response.body)

        m = re.compile('<em>(.*?)</em>', flags=re.DOTALL)

        for student in students:
            majors = m.findall(student[2])
            name = student[0].strip()
            email = student[1].strip()
            major1 = lget(majors, 0, '')
            major2 = lget(majors, 1, '')
            major3 = lget(majors, 2, '')

            yield StudentItem(
                name=name,
                email=email,
                major1=major1,
                major2=major2,
                major3=major3
            )
