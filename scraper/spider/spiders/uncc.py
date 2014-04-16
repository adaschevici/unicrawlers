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

class UnccSpider(StudentSpider):
    name = 'uncc'
    start_urls = ['http://search.uncc.edu/people/index.cfm']

    def __init__(self, *args, **kwargs):
        super(UnccSpider, self).__init__(*args, **kwargs)
        dispatcher.connect(self.idle, signals.spider_idle)

    def idle(self, spider):
        self.state['progress_current'] = self.state['progress_total']

    def parse(self, response):
        if self.search_type == 'letters':
            self.search_type = 'letters-simple'

        phrases = self.get_search_phrases()

        self.state['progress_current'] = 0
        self.state['progress_total'] = len(phrases)

        for phrase in phrases:
            yield self.get_search_request(response, str(phrase))

    def get_search_request(self, response, phrase):
        return Request(
            url='http://search.uncc.edu/people/index.cfm?p=search&role=1&firstname=&lastname=%s&term=201380' % (phrase,),
            callback=self.people
        )

    def people(self, response):
        p = re.compile('<div[^>]+>([^<]+)</div>[^<]+<table[^>]+>[^<]+<tr>[^>]+>[^>]+>[^>]+[^>]+>: ([^<]+)<BR>[^>]+>[^>]+>: ([^<]+)</td>[^<]+<[^<]+<[^>]+>([^<]+)')
        students = p.findall(response.body)

        for student in students:
            name = student[0].strip()
            major = student[1].strip()
            degree = student[2].strip()
            email = student[3].strip()

            yield StudentItem(
                name=name,
                major1=major,
                degree=degree,
                email=email
            )

        sel = Selector(response)
        pages = sel.xpath('//*[@id="tm-primary"]/div[4]/div/a')

        for page in pages:
            if 'Next' in page.xpath('.//text()').extract()[0]:
                yield Request(
                    url='http://search.uncc.edu%s' % page.xpath('.//@href').extract()[0],
                    callback=self.people
                )
                break

