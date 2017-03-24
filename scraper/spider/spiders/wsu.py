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

class WsuSpider(StudentSpider):
    name = 'wsu'
    start_urls = ['http://search.wsu.edu/advanced.aspx']

    def __init__(self, *args, **kwargs):
        super(WsuSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        if self.search_type == 'letters':
            self.search_type = 'letters-two'

        phrases = self.get_search_phrases()

        self.state['progress_current'] = 0
        self.state['progress_total'] = len(phrases)

        phrases = ['ab']

        for phrase in phrases:
            yield self.get_search_request(response, str(phrase))

    def get_search_request(self, response, phrase):
        return Request(
            url='http://search.wsu.edu/advanced.aspx?cx=004677039204386950923%%3xvo7gapmrrg&cof=FORID%%3A11&q=%s&sa=Search&sb=2' % phrase, 
            callback=self.students
        )

    def students(self, response):
        sel = Selector(response)

        p = re.compile('<strong>(.+?)</strong></td></tr><tr><td>(.+?)</td>.*?mailto:(.+?)"')
        students = p.findall(response.body)
        print response.url
        print students
