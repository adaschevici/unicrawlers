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
from spider.utils import Sanitizer

from string import ascii_lowercase
from itertools import product

alphabet = list(ascii_lowercase)
two_letter_words = list(product(alphabet, alphabet))
output_dir = os.path.join(os.getenv('HOME'), 'temp_files')
if not os.path.isdir(output_dir):
    os.mkdir(output_dir)

class StudentSpider(BaseSpider):
    def __init__(self, *args, **kwargs):
        self.letters = kwargs.get('letters', [])
        self.words = kwargs.get('words', None)
        self.search_type = kwargs.get('search_type', 'letters')
        self.output_file = kwargs.get('output_file', None)
        self.input_file = kwargs.get('input_file', None)
        self.proxy_file = kwargs.get('proxy', None)
        self.interval = kwargs.get('interval', 1000)
        self.proxy_interval = kwargs.get('proxy_interval', 4)
        self.job = kwargs.get('_job', None)

        if not isinstance(self.letters, list):
            self.letters = self.letters.split(',')

        self.output_file = os.path.join(output_dir, self.output_file)

    def get_search_phrases(self):
        if self.search_type == 'letters':
            phrases = []

            for letter in self.letters:
                for word in two_letter_words:
                    phrases.append('%c%c%c' % (letter, word[0], word[1],))

            return phrases
        elif self.search_type == 'letters-two':
            phrases = []

            for letter in self.letters:
                for letter2 in alphabet:
                    phrases.append('%c%c' % (letter, letter2,))

            return phrases
        elif self.search_type == 'letters-simple':
            phrases = []

            for letter in self.letters:
                phrases.append('%c' % (letter,))

            return phrases
        elif self.search_type == 'file':
            text_file = open(self.input_file, "r")
            self.words = [word.strip() for word in text_file.readlines()]
            text_file.close()

            return self.words
        elif self.search_type == 'file-letter':
            text_file = open(self.input_file, "r")
            words = [word.strip() for word in text_file.readlines()]
            text_file.close()
            phrases = []

            for word in words:
                for letter in alphabet:
                    phrases.append(('%c' % letter, '%s' % Sanitizer.trim(word)))

            # print phrases
            return phrases

    def get_progress(self):
        if not 'progress_total' in self.state or not self.state['progress_total']:
            return 0
        return int(float(self.state['progress_current']) / float(self.state['progress_total']) * 100) 
