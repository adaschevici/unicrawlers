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

class WfuSpider(StudentSpider):
    name = 'wfu'
    start_urls = ['https://win.wfu.edu/win/app.dirx.ExternalDirectory']

    def __init__(self, *args, **kwargs):
        super(WfuSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        if self.search_type == 'letters':
            self.search_type = 'letters-simple'

        phrases = self.get_search_phrases()

        self.state['progress_current'] = 0
        self.state['progress_total'] = len(phrases)

        for phrase in phrases:
            yield self.get_search_request(response, str(phrase))

    def get_search_request(self, response, phrase):
        return FormRequest.from_response(response,
            formdata={
                'fullName': phrase,
                'assocType': 'student',
                'submit_button': 'Search',
                'action': 'doExternalSearch',
                'listing': '',
                'assocTypeLast': ''
            },
            formname='dirform',
            dont_click=True,
            callback=self.students
        )

    def get_student_details_request(self, response, id): 
        return FormRequest.from_response(response,
            formdata={
                'fullName': '',
                'assocType': 'student',
                'action': 'showListing',
                'listing': id,
                'assocTypeLast': 'student'
                },
            dont_click=True,
            formname='dirform',
            callback=self.student_info
        )

    def students(self, response):
        sel = Selector(response)
        students = sel.xpath('//*[@id="dirform"]/table[2]//tr/td/a')
        #from scrapy.shell import inspect_response
        #inspect_response(response)

        self.state['progress_current'] += 1
        self.state['progress_total'] += len(students)
        
        for student in students:
            yield self.get_student_details_request(response, student.re('(\d+.\d+)')[0])

    def student_info(self, response):
        sel = Selector(response)
        info = sel.xpath('//*[@id="dirform"]/table[2]/tr')

        data = {}

        self.state['progress_current'] += 1

        # skipping table header ([1:])
        for i in info[1:]:
            try:
                property_name = i.xpath('.//td[1]/text()').extract()[0]
                property_value = i.xpath('.//td[2]/text()').extract()[0]

                data[property_name.strip()] = property_value.strip()
            except IndexError:
                # probably email
                property_name = i.xpath('.//td[1]/text()').extract()[0]

                if property_name == 'Email':
                    data[property_name.strip()] = i.xpath('.//td[2]/a/text()').extract()[0].strip()
        
        if 'Name' in data and 'Email' in data:
            yield StudentItem(
                name=data['Name'],
                email=data['Email'],
                campus=data.get('Campus Address', '')
            )
