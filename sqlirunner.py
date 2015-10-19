# coding=utf-8

from config import SERVER
from autosqli import AutoSqli
from urlparse import urlparse

class SqliRunner(object):
    """
    SqliRunner is used to detect a request from proxy is 
    injectable or not.
    """
    def __init__(self, request):
        self.request = request
        self.url = request.url
        self.data = request.body
        self.cookie = self.get_from_headers('cookie')
        self.referer = self.get_from_headers('referer')
        self.req_text = self.get_raw_request(self.request)

    def get_raw_request(self, request):
        """
        Get raw http request body
        """
        text = ""
        method = request.method
        url = request.url
        urlp = urlparse(url)
        body = request.body
        headers = request.headers
        protocol = 'HTTP/1.1'
        if not urlp.fragment and not urlp.query:
            link = "%s" % urlp.path
        elif not urlp.fragment:
            link = "%s?%s" % (urlp.path, urlp.query)
        elif not urlp.query:
            link = "%s#%s" % (urlp.path, urlp.fragment)
        else:
            link = "%s?%s#%s" % (urlp.path, urlp.query, urlp.fragment)
        text += "%s %s %s\r\n" % (method, link, protocol)
        for h in headers.get_all():
            text += "%s: %s\r\n" % (h[0], h[1])
        text += "\r\n"
        if body: text += body
        return text

    def get_from_headers(self, key):
        try:
            item = self.request.headers.get_list(key)
            if not item: 
                return ''
            else:
                return item[0]
        except Exception, e:
            return ''

    def run(self):
        """
        Run the sqli detection using HTTPRequest object.
        """
        try:
            detecter = AutoSqli(SERVER, self.url, self.data, 
                self.referer, self.cookie, self.req_text) 
            detecter.deamon = True
            detecter.start()
        except Exception, e:
            print e
