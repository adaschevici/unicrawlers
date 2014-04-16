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

class CmichSpider(StudentSpider):
    name = 'cmich'
    start_urls = ['https://www.cmich.edu/search/pages/peopleresults.aspx']

    def __init__(self, *args, **kwargs):
        super(CmichSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        phrases = self.get_search_phrases()

        self.state['progress_current'] = 0
        self.state['progress_total'] = len(phrases)

        for phrase in phrases:
            yield self.get_search_request(response, str(phrase))

    def get_search_request(self, response, phrase):
        return FormRequest.from_response(response,
            formdata={
                'ctl00$SPWebPartManager1$g_a27adfaf_8519_4c39_a3c9_495e9b106eae$ctl00$tbPeopleQuery': phrase,
                'ctl00$SPWebPartManager1$g_a27adfaf_8519_4c39_a3c9_495e9b106eae$ctl00$btnPeopleGo': 'Search',
                'ctl00$SPWebPartManager1$g_a27adfaf_8519_4c39_a3c9_495e9b106eae$ctl00$rblFilter': 's'
            },
            dont_click=True,
            callback=self.people
        )

    def people(self, response):
        sel = Selector(response)
        students = sel.xpath('//td[@class="cmuDirResultsInfo"]')

        self.state['progress_current'] += 1
        
        for student in students:
            yield StudentItem(
                name=student.xpath('.//div[@class="cmuDirName"]/text()').extract()[0],
                email=student.xpath('.//div[@class="cmuDirContact"]/a/text()').extract()[0]
            )
