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

class SceduSpider(StudentSpider):
    name = 'scedu'
    start_urls = ['http://www.sc.edu/about/directory/']
