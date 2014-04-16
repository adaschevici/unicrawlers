import os
import settings

from scrapy import signals
from scrapy.exceptions import DropItem
from scrapy.contrib.exporter import CsvItemExporter

from utils import Url, Utf8

class AlreadyScraped(DropItem):
    pass

class StudentPipeline(object):
    def __init__(self):
        self.files = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        try:
            size = os.path.getsize(spider.output_file)
        except:
            size = 0
        spider.log("<"*10)
        spider.log(spider.output_file)
        spider.log("<"*10)
        file_out = open(spider.output_file, 'a+b')
        self.files[spider] = file_out
        self.exporter = CsvItemExporter(file_out, delimiter='|')
        self.exporter._headers_not_written = size == 0
        self.exporter.fields_to_export = ['name', 'email', 'campus', '_class', 'address', 'city', 'major1', 'major2', 'major3', 'college', 'department', 'phone', 'level', 'enrollment']
        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        file = self.files.pop(spider)
        file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item
