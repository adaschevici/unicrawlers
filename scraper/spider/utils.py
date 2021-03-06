import cgi, urllib, urlparse
import re
# helper class for modifying urls
# source: http://stackoverflow.com/a/2878051/250162
class Url(object):
    def __init__(self, url):
        """Construct from a string."""
        self.scheme, self.netloc, self.path, self.params, self.query, self.fragment = urlparse.urlparse(url)
        self.args = dict(cgi.parse_qsl(self.query))

    def __str__(self):
        """Turn back into a URL."""
        self.query = urllib.urlencode(self.args)
        self.query = urllib.unquote(self.query)
        return urlparse.urlunparse((self.scheme, self.netloc, self.path, self.params, self.query, self.fragment))


# helper class for safe utf8 conversion of page content
class Utf8(object):
    def __init__(self, page):
        """Safe conversion of page to utf"""
        try:
            self.page = page.encode("utf8")
        except UnicodeDecodeError:
            self.page = page.decode('iso-8859-1').encode('utf8')

    def __str__(self):
        """Convert page to str"""
        return str(self.page)


class Sanitizer(object):

    exclusions = ['\t', '\xa0', '"']
    replacements = ['\r\n']

    @classmethod
    def trim(cls, data):
        try:
            for exc in cls.exclusions:
                data = re.sub(exc, '', data, flags=re.UNICODE)
            for exc in cls.replacements:
                data = re.sub(exc, ' ', data, flags=re.UNICODE)
            data = data.strip()
        except:
            pass
        return data or 'N/A'

if __name__ == '__main__':
    test = ' \t \t \t \t caca'
    data = None
    print test
    print Sanitizer.trim(test)
    print data or 'none'