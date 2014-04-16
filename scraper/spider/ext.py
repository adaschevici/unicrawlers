import time
import redis
from scrapy import log
from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.exceptions import CloseSpider

class SpiderTimeReport(object):

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()

        # connect the extension object to signals
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)

        return ext

    def spider_opened(self, spider):
        spider.started_on = time.time()

    def spider_closed(self, spider):
        work_time = int(time.time() - spider.started_on)
        fmt_time = time.strftime('%H:%M:%S', time.gmtime(work_time))
        
        spider.log("Spider finished crawling after %s." % fmt_time, level=log.INFO)


class CloseSpider(object):
    def __init__(self, crawler):
        self.crawler = crawler
        self.stats = crawler.stats

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(crawler)

        # connect the extension object to signals

        crawler.signals.connect(ext.item_dropped, signal=signals.item_dropped)
        crawler.signals.connect(ext.response_received, signal=signals.response_received)

        return ext

    def item_dropped(self, item, spider, exception):
        if hasattr(spider, 'dropped_items_limit'):
            dropped_count = self.stats.get_value('item_dropped_count')
            scraped_count = self.stats.get_value('item_scraped_count')
            limit = spider.dropped_items_limit

            if limit and dropped_count >= limit and scraped_count <= 1:
                self.crawler.engine.close_spider(spider, 'Reached the limit of dropped items (%d). Aborting.' % limit)

    def response_received(self, response, request, spider):
        if hasattr(spider, 'request_limit'):
            limit = int(spider.request_limit)
            request_count = int(self.stats.get_value('downloader/request_count'))

            if limit and request_count >= limit:
                self.crawler.engine.close_spider(spider, 'Reached the limit of requests (%d). Aborting.' % limit)            

class GenteProgressReporter(object):

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()

        # connect the extension object to signals
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.response_received, signal=signals.response_received)

        return ext

    def spider_opened(self, spider):
        self.r = redis.StrictRedis(host='localhost', port=6379, db=0)

    def spider_closed(self, spider):
        # TODO: close redis connection
        self.save_progress(spider)

    def response_received(self, response, request, spider):
        self.save_progress(spider)

    def save_progress(self, spider):
        self.r.set('job:%s:progress' % spider.job, spider.get_progress())
        print spider.get_progress()
        print spider.job
