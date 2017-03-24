import os
import re

from twisted.internet import reactor, defer
from scrapy.selector import Selector
from spider.items import StudentItem
from scrapy.http import FormRequest
from scrapy.http import Request
from spider.spiders.basic import StudentSpider
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals


class XPATHS:

    pass

class NcsuSpider(StudentSpider):
    name = 'ncsu'
    start_urls = ['http://www.ncsu.edu/directory/']

    def idle(self, spider):
        self.state['progress_current'] = self.state['progress_total']

    def __init__(self, *args, **kwargs):
        super(NcsuSpider, self).__init__(*args, **kwargs)
        dispatcher.connect(self.idle, signals.spider_idle)

    def parse(self, response):
        phrases = self.get_search_phrases()

        self.state['progress_current'] = 0
        self.state['progress_total'] = len(phrases)
        for phrase in phrases:
            yield self.get_search_request(response, str(phrase))

    def get_search_request(self, response, phrase):
        return Request(
            url='http://www.ncsu.edu/directory/?lastnametype=starts&lastname=%s&firstnametype=starts&firstname=&emailaddresstype=equals&emailaddress=&addresstype=contains&address=&phonenumbertype=ends&phonenumber=&departmenttype=contains&department=&titletype=contains&title=&searchtype=%s&matchnicks=on&includevcard=on&matchprevlast=on&order=mixed&style=normal&search=Search' % (phrase,),
            callback=self.people
        )

    def people(self, response):
        sel = Selector(response)
