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
from scrapy.utils.markup import replace_tags


class XPATHS:

    DEPTS_NUM = "//div[@class='user_content']/h3/text()"
    DEPARTMENTS = "(//div[@class='user_content']/h3[%s])"
    DEPT_TABLE = "./following-sibling::table[1]"
    TABLE_LINKS = ".//tr//td[1]/a/@href"

    PERSON_TABLE = "//table[@class='facstaff tablespecial']"
    PERSON_NAME = ".//tr[contains(., 'Name')]//td/text()"
    PERSON_DEPT = ".//tr[contains(., 'Department')]//td/text()"
    PERSON_TITLE = ".//tr[contains(., 'Title')]//td/text()"
    PERSON_LOCATION = ".//tr[contains(., 'Location')]//td/text()"
    PERSON_CAMPUS_BOX = ".//tr[contains(., 'Campus Box')]//td/text()"
    PERSON_PHONE = ".//tr[contains(., 'Phone')]//td/text()"
    PERSON_EMAIL = ".//tr[contains(., 'Name')]//td/text()"
    PERSON_WMID = ".//tr[contains(., 'WMuserid')]//td/text()"


class CONSTANTS:

    BASE_URL = "http://directory.wm.edu/people/"


class WmuniSpider(StudentSpider):
    name = 'wmuni'
    start_urls = ['http://directory.wm.edu/people/']

    def process_queue(self, response=None):
        if self.state['page_queue']:
            return self.state['page_queue'].pop()
        if self.state['phrases']:
            if not response:
                return Request(url=WmuniSpider.start_urls[0],
                               callback=self.process_queue,
                               dont_filter=True)
            else:
                self.state['progress_current'] += 1
                phrase = self.state['phrases'].pop()
                return self.get_search_request(response, str(phrase))

    def idle(self, spider):
        if spider != self:
            return

        request = self.process_queue()

        if request:
            self.crawler.engine.crawl(request, spider=self)
        else:
            self.state['progress_current'] = self.state['progress_total']

    def __init__(self, *args, **kwargs):
        super(WmuniSpider, self).__init__(*args, **kwargs)
        dispatcher.connect(self.idle, signals.spider_idle)

    def parse(self, response):
        self.phrases = self.get_search_phrases()

        # from scrapy.shell import inspect_response
        # inspect_response(response)

        self.state['phrases'] = self.get_search_phrases()
        self.state['progress_current'] = 0
        self.state['progress_total'] = len(self.state['phrases'])
        self.state['page_queue'] = []
        return self.process_queue()
        # for phrase in phrases:
        #     yield self.get_search_request(response, str(phrase))

    def get_search_request(self, response, phrase):
        self.log('>>>>>>>>>>>>>>>>>>%s>>>>>>>>>>>>>>>>>>>>>' % phrase)
        return FormRequest(
            url='http://directory.wm.edu/people/namelisting.cfm',
            formdata={
                'searchtype': 'last',
                'criteria': 'starts',
                'phrase': phrase
            },
            callback=self.people
        )

    def people(self, response):
        selector = Selector(response)
        dept_no = len(selector.xpath(XPATHS.DEPTS_NUM).extract())
        meta = {}
        self.log('Reached line 98')
        self.log('>>>>>>>>>>>>>>>>>>%s>>>>>>>>>>>>>>>>>>>>>' % dept_no)
        for dept in xrange(dept_no):
            self.log(XPATHS.DEPARTMENTS % (dept + 1))
            dept_tbl = selector.xpath(XPATHS.DEPARTMENTS % (dept + 1))
            try:
                meta['department'] = replace_tags(dept_tbl.extract()[0])
            except IndexError:
                self.log(dept_tbl.extract()+['>>>>>>>>>>>>>>>>>>>>'])
            dept_table = dept_tbl.xpath(XPATHS.DEPT_TABLE)
            self.log('Reached line 106')
            for dept_tbl_sect in dept_table:
                self.log('Reached line 107')
                table_links = dept_tbl_sect.xpath(XPATHS.TABLE_LINKS).extract()
                self.log('****************%s********************' % len(table_links))
                for link in table_links:
                    self.log(link)
                    yield Request(
                        url=CONSTANTS.BASE_URL + link,
                        callback=self.parse_people,
                        meta=meta
                    )

    def parse_people(self, response):
        def lget(x, index, default):
            return x[index] if len(x) > index else default
        self.log("Entered parse poeple")
        department = response.meta.get('department', '')
        selector = Selector(response)
        name = lget(selector.xpath(XPATHS.PERSON_NAME).extract(), 0, '')
        email = lget(selector.xpath(XPATHS.PERSON_EMAIL).extract(), 0, '')
        title = lget(selector.xpath(XPATHS.PERSON_TITLE).extract(), 0, '')
        # wmid = lget(selector.xpath(XPATHS.PERSON_WMID), 0, '')
        dept = department
        location = lget(selector.xpath(XPATHS.PERSON_LOCATION).extract(), 0, '')
        phone_num = lget(selector.xpath(XPATHS.PERSON_PHONE).extract(), 0, '')
        yield StudentItem(
            name=name,
            email=email,
            degree=title,
            department=dept,
            phone=phone_num,
            address=location
        )