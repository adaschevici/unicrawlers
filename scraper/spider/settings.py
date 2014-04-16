# Scrapy settings for spider project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'spider'

SPIDER_MODULES = ['spider.spiders']
NEWSPIDER_MODULE = 'spider.spiders'

ITEM_PIPELINES = [
    'spider.pipelines.StudentPipeline'
]

EXTENSIONS = {
    'spider.ext.SpiderTimeReport': 500,
    'spider.ext.CloseSpider': 500,
    'spider.ext.GenteProgressReporter': 500
}

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'spider (+http://www.yourdomain.com)'
