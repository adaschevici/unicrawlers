# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class StudentItem(Item):
    name = Field()
    email = Field()
    phone = Field()
    campus = Field()
    _class = Field()
    address = Field()
    city = Field()
    major1 = Field()
    major2 = Field()
    major3 = Field()
    college = Field()
    degree = Field()
    department = Field()
    level = Field()
    enrollment = Field()
