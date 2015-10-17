#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
基于Tornado实现的HTTP代理
浏览器设置代理为8080即可
"""

import copy
import time
import socket
import subprocess

import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.escape as escape

from urlparse import urlparse
from tornado.options import define, options

define("port", default=8080, help="run on the given port", type=int)

class ProxyHandler(tornado.web.RequestHandler):
    '''
    HTTP代理实现类
    '''
    def render_request(self, url, callback=None, **kwargs):
        '''
        使用AsyncHTTPClient异步客户端发送http请求
        '''
        req = tornado.httpclient.HTTPRequest(url, **kwargs)
        asy_client = tornado.httpclient.AsyncHTTPClient()
        asy_client.fetch(req, callback)

    # 设置tornado支持connect方法
    SUPPORTED_METHODS = ("GET", "HEAD", "POST", "DELETE", "PATCH", "PUT",
                         "OPTIONS", "CONNECT")
    @tornado.web.asynchronous
    def get(self):
        # 获取请求体
        body = self.request.body
        if not body:
            body = None
        try:
            # 代理发送请求
            # 设置超时时间为12E4防止poll2的访问超时
            # 导致重复登录问题
            timeout = 5
            if "poll2" in self.request.uri:
                timeout = 12E4
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
        异步HTTP请求的回调函数
        '''
        # 处理异常情况
        if response.error and type(response.error) != tornado.httpclient.HTTPError:
            self.set_status(500)
            self.write('Internal server error:\n' + str(response.error))
            self.finish()
        else:
            # 处理正常情况
            try:
                self.set_status(response.code)
            except ValueError, e:
                print '[ValueError]:%s' % str(e)
            # 设置RequestHandler中的self._headers属性
            headers = self._headers.keys()
            for header in headers:
                value = response.headers.get(header)
                if value:
                    self.set_header(header, value)
            # 设置set-cookie头
            cookies = response.headers.get_list('Set-Cookie')
            if cookies:
                for i in cookies:
                    self.add_header('Set-Cookie', i)
            try:
                if response.code != 304:
                    self.write(response.body)
            except TypeError, e:
                print '[TypeError]:%s' % str(e)
            self.finish()

    @tornado.web.asynchronous
    def post(self):
        self.get()

    @tornado.web.asynchronous
    def connect(self):
        '''
        对于HTTPS连接，代理应当作为TCP中继
        '''
        print 'Starting Conntect to %s' % self.request.uri
        # 获取request的socket
        req_stream = self.request.connection.stream

        # 找到主机端口，一般为443
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
            '''
            创建TCP中继的回调
            '''
            print 'CONNECT tunnel established to %s' % self.request.uri
            req_stream.read_until_close(req_close, write_to_server)
            conn_stream.read_until_close(proxy_close, write_to_client)
            req_stream.write(b'HTTP/1.0 200 Connection established\r\n\r\n')

        # 创建iostream
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        conn_stream = tornado.iostream.IOStream(s)
        conn_stream.connect((host, port), on_connect)

if __name__ == '__main__':
    tornado.options.parse_command_line()
    print "Starting Proxy on port %s" % options.port
    handlers = [
        (r'.*', ProxyHandler),
    ]
    app = tornado.web.Application(handlers=handlers)
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
