import os
import re

from twisted.internet import reactor, defer
from scrapy.selector import Selector
from spider.items import StudentItem
from scrapy.http import Request
from scrapy.http import FormRequest
from spider.spiders.basic import StudentSpider
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from scrapy.utils.markup import replace_tags

class XPATHS:

    STUDENTS_TABLE = "//table[@class='bordertable']//tr"
    EMAIL = "./td[last()]//a/text()"
    NAME = "./td[1]"
    DEPARTMENT = "./td[2]/text()"
    PHONE = "./td[3]/text()"


class CaseSpider(StudentSpider):
    name = 'case'
    start_urls = ['https://webapps.case.edu/directory/index.html']

    def __init__(self, *args, **kwargs):
        super(CaseSpider, self).__init__(*args, **kwargs)
        self.filter_role = kwargs.get('filter_role', 'A')
        dispatcher.connect(self.idle, signals.spider_idle)
