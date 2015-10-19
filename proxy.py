#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ProxyHandler is a http proxy based on Tornado. The default port is 8080.
Run this command to run the proxy:
    python proxy --port=8080
Use the `port` option to change the proxy's port.
"""

import sys
import socket

import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.web

from models import *
from urlparse import urlparse
from sqlirunner import SqliRunner

domain = ""
urls_pool = set()
blacklist = []

class ProxyHandler(tornado.web.RequestHandler):
    '''
    A http proxy based on RequestHandler
    '''
    def render_request(self, url, callback=None, **kwargs):
        '''
        Use `AsyncHTTPClient` send http request
        '''
        req = tornado.httpclient.HTTPRequest(url, **kwargs)
        asy_client = tornado.httpclient.AsyncHTTPClient()
        asy_client.fetch(req, callback)

    # Set supported methods for proxy
    SUPPORTED_METHODS = ("GET", "HEAD", "POST", "DELETE", "PATCH", "PUT",
                         "OPTIONS", "CONNECT")
    @tornado.web.asynchronous
    def get(self):
        # get request body
        body = self.request.body
        if not body:
            body = None
        try:
            # send request by proxy
            timeout = 5
            # proxy sends the request
            self.render_request(
                    self.request.uri, 
                    callback=self.on_response,
                    method=self.request.method,
                    body=body, 
                    headers=self.request.headers,
                    request_timeout=timeout,
                    follow_redirects=True,
                    allow_nonstandard_methods=True)
        except tornado.httpclient.HTTPError as httperror:
            if hasattr(httperror, 'response') and httperror.response:
                self.on_response(httperror.response)
            else:
                self.set_status(500)
                self.write('Internal server error:\n' + str(httperror))
                self.finish()

    def on_response(self, response):
        '''
        http requst callback
        '''
        global domain, urls_pool, blacklist
        # handle exceptions
        if response.error and type(response.error) != tornado.httpclient.HTTPError:
            self.set_status(500)
            self.write('Internal server error:\n' + str(response.error))
            self.finish()
        else:
            # run the sqlmap
            # only detect few content type:
            # text/html, application/json
            url = response.request.url
            method = response.request.method
            urlp = urlparse(url)
            host_path = "%s://%s/%s" % (urlp.scheme, urlp.netloc, urlp.path)
            content_type = response.headers.get_list('content-type')
            if len(content_type) > 0:
                content_type = content_type[0]
            # default domain is null
            if not domain:
                if (method == 'GET' and urlp.query) or \
                    (method == 'POST' and response.body):
                    if ("text/html" in content_type) or \
                        ("application/json" in content_type):
                        if (host_path not in urls_pool) and  \
                            (urlp.netloc not in blacklist) and \
                            (response.code == 200):
                            urls_pool.add(host_path)
                            sqli_runner = SqliRunner(response.request)
                            sqli_runner.run()
            # only detect the POST method and the GET 
            # method with query string in url
            elif (method == 'GET' and urlp.query) or \
                (method == 'POST' and response.body):
                if urlp.netloc.endswith(domain) and (host_path not in urls_pool) \
                    and response.code == 200 and (urlp.netloc not in blacklist):
                        if ("text/html" in content_type) or \
                            ("application/json" in content_type):
                            urls_pool.add(host_path)
                            sqli_runner = SqliRunner(response.request)
                            sqli_runner.run()

            try:
                self.set_status(response.code)
            except ValueError, e:
                pass
                # print '[ValueError]:%s' % str(e)
            # Set `self._headers` attribute for RequestHandler
            headers = self._headers.keys()
            for header in headers:
                value = response.headers.get(header)
                if value:
                    self.set_header(header, value)
            # set the `set-cookie` header
            cookies = response.headers.get_list('Set-Cookie')
            if cookies:
                for i in cookies:
                    self.add_header('Set-Cookie', i)
            try:
                if response.code != 304:
                    self.write(response.body)
            except TypeError, e:
                pass
                # print '[TypeError]:%s' % str(e)
            self.finish()

    @tornado.web.asynchronous
    def post(self):
        self.get()

    @tornado.web.asynchronous
    def connect(self):
        # 获取request的socket
        req_stream = self.request.connection.stream

        # get port
        host, port = self.request.uri.split(':')
        port = int(port)

        def req_close(data=None):
            if conn_stream.closed():
                return
            if data:
                conn_stream.write(data)
            conn_stream.close()

        def write_to_server(data):
            conn_stream.write(data)
        
        def proxy_close(data=None):
            if req_stream.closed():
                return
            if data:
                req_stream.write(data)
            req_stream.close(data)

        def write_to_client(data):
            req_stream.write(data)

        def on_connect():
            req_stream.read_until_close(req_close, write_to_server)
            conn_stream.read_until_close(proxy_close, write_to_client)
            req_stream.write(b'HTTP/1.0 200 Connection established\r\n\r\n')

        # 创建iostream
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        conn_stream = tornado.iostream.IOStream(s)
        conn_stream.connect((host, port), on_connect)

if __name__ == '__main__':
    create_tables()
    with open('blacklist.txt', 'r') as f:
        blacklist = f.readlines()
    blacklist = [i.replace("\n", "") for i in blacklist]
    port = 8080
    if len(sys.argv) == 3:
        port = int(sys.argv[1])
        domain = sys.argv[2]
    print "Starting Proxy on port %s, domain %s" % (port, domain)
    handlers = [
        (r'.*', ProxyHandler),
    ]
    app = tornado.web.Application(handlers=handlers)
    app.listen(port)
    tornado.ioloop.IOLoop.instance().start()
