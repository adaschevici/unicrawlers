# -*- coding: utf-8 -*- 
import os
import re
import urlparse

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
from scrapy.utils.response import get_base_url

class UokSpider(StudentSpider):
    name = 'uok'
    start_urls = ['https://myidentity.ku.edu/directory/search']

    def __init__(self, *args, **kwargs):
        super(UokSpider, self).__init__(*args, **kwargs)
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
        return FormRequest(
            url='https://myidentity.ku.edu/directory/search',
            formdata={
                'searchfor_name': phrase,
                'liveSearch': 'off',
                'command': 'simple',
                'Search': 'Search'
            },
            callback=self.people
        )

    def people(self, response):
        self.state['progress_current'] += 1

        sel = Selector(response)
        students = sel.xpath('//*[@id="searchResults"]/div/div[2]/table/tr/td[1]/a/@href').extract()

        for url in students:
            # convert relative urls to absolute
            base_url = get_base_url(response)
            url = urlparse.urljoin('https://myidentity.ku.edu', url)

            yield Request(url=url, callback=self.people_details)

    def people_details(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default

        sel = Selector(response)
        name = sel.xpath('//*[@id="mainbody"]/h4/text()').re(r'(.*?) \[')[0]
        ai = sel.xpath('//*[@id="mainbody"]/table/tr/td[2]/text()').extract()
        address = lget(ai, 0, '')
        city = lget(ai, 1, '')
        email = sel.xpath('//*[@id="mainbody"]/ul/li/a/text()').extract()[0]

        yield StudentItem(
            name=name,
            email=email,
            city=city,
            address=address
        )


