import asyncio
import os
import threading
from abc import ABC

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

from ssh_server import SSH


class IndexHandler(tornado.web.RequestHandler, ABC):
    def get(self):
        self.render('index.html')


class WebSocketHandler(tornado.websocket.WebSocketHandler, ABC):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.ssh = None

    def check_origin(self, origin):
        return True

    def _reading(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        while True:
            try:
                data = self.ssh.read()
                if data:
                    res = {'data': data.decode('utf-8')}
                    self.write_message(res)
            except Exception as e:
                print(e)
                self.write_message({'data': ''})

    def open(self):
        args = self.request.arguments
        host = args["h"][0]
        port = int(args["p"][0])
        username = args["u"][0]
        passwd = args["passwd"][0]
        self.ssh = SSH(host, port, username, passwd)
        if self.ssh.chan:
            t = threading.Thread(target=self._reading)
            t.setDaemon(True)
            t.start()
        else:
            self.write_message({'data': 'auth failed'})

    def on_message(self, message):
        try:
            self.ssh.send(message)
        except Exception as e:
            print(e)

    def on_close(self):
        print("WebSocket 关闭")
        self.ssh.close()


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', IndexHandler),
            (r'/ws', WebSocketHandler)
        ]

        settings = {
            "template_path": os.path.join(os.path.dirname(__file__), "templates"),
            "static_path": os.path.join(os.path.dirname(__file__), "static"),
        }
        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == '__main__':
    app = Application()
    server = tornado.httpserver.HTTPServer(app)
    server.listen(9040)
    tornado.ioloop.IOLoop.instance().start()
