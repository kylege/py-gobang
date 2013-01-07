import tornado
from tornado import web
from datetime import timedelta
import os
from Gobang import Gobang, GameRoom
import random


class FlushHandler(web.RequestHandler):

    @web.asynchronous
    def get(self):
        self.write({'result':True, 'msg':'yes'})
        self.flush()
        tornado.ioloop.IOLoop.instance().add_timeout(timedelta(seconds=2), self._flush)


    def _flush(self):
        self.write({'result':True, 'msg':'yes'})
        self.flush
        self.finish()

class IndexHandler(web.RequestHandler):
    def get(self):
        self.render('index.html')

class EnterRoomHandler(web.RequestHandler):

    def get(self, room_name):
        if not room_name in all_rooms.keys(): #新房间
            piece_id = random.randint(1,2)
            self.set_secure_cookie('up', str(piece_id))
            room = GameRoom(room_name, piece_id)
            all_rooms[room_name] = room
        else:
            up = self.get_secure_cookie('up')
            self.write(up)
        

urls = [
        (r"/", IndexHandler),
        (r"/flush", FlushHandler),
        (r"/room-(.*)", EnterRoomHandler),
        ]

settings = dict(
        template_path = os.path.join(os.path.dirname(__file__), "templates"),
        static_path = os.path.join(os.path.dirname(__file__), "static"),
        cookie_secret = 'werwerwAW15Wwr-wrwe==dssdtfrwerter2t12',
        );

gobang = Gobang()
room = GameRoom('test')
all_rooms = {'test':room}

def main():
    application = web.Application(urls, **settings)

    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
