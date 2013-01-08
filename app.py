#encoding=utf8
#用apt-get install python-tornado安装的不是最新，有bug。要用 pip install tornado

import os
from Gobang import Gobang, GameRoom
import random

import zmq
from zmq.eventloop import zmqstream, ioloop
ioloop.install()

import tornado
from tornado import web

class EnterRoomHandler(web.RequestHandler):
    # @web.asynchronous
    def get(self, room_name):
        if not room_name in all_rooms.keys(): #新房间
            piece_id = random.randint(1,2)
            self.set_secure_cookie('up', str(piece_id))  #棋子颜色号，你是黑棋还是白棋，随机分配
            self.set_secure_cookie('rn', room_name) #房间名称
            room = GameRoom(room_name, piece_id)
            all_rooms[room_name] = room
            self.render('index.html', cur_room=room, my_piece_id=piece_id, is_waiting=True,
                all_rooms_count=len(all_rooms),
                )
            print '第一个进入'
        else:
            cur_room = all_rooms[room_name]
            if len(cur_room.user_piece_ids) == 2: #已经满了
                readonly = True
                self.write('房间已被占用')
                print '房间已被占用'
            elif len(cur_room.user_piece_ids) == 1:
                my_piece_id = 1 in cur_room.user_piece_ids and 2 or 1
                cur_room.user_piece_ids.add(my_piece_id)
                self.set_secure_cookie('up', str(my_piece_id))
                self.set_secure_cookie('rn', room_name)
                cur_room.status = GameRoom.STATUS_GOING
                topic = (room_name+''+str(my_piece_id)).encode('UTF-8')
                pubContent([topic,'start,'])
                self.render('index.html', cur_room=cur_room, my_piece_id=my_piece_id, is_waiting=(my_piece_id==2), 
                    all_rooms_count=len(all_rooms),
                    )
                print '游戏开始'

'''
    下棋
'''
class GameStepHandler(web.RequestHandler):
    
    def post(self):
        pos = self.get_argument('pos')
        if not pos:
            self.write({'result':False, 'msg':'pos is empty'})
            self.finish()
        posarr = pos.split(',')
        if not posarr or not len(posarr) == 2:
            self.write({'result':False, 'msg':'pos is invalid'})
            self.finish()
        room_name = self.get_argument('room_name')
        if not room_name in all_rooms.keys(): 
            self.write({'result':False, 'msg':'room not exists'})
            self.finish()
        cur_room = all_rooms[room_name]
        if not cur_room.status == GameRoom.STATUS_GOING:
            self.write({'result':False, 'msg':'room not going'})
            self.finish()
        user_piece = self.get_secure_cookie('up')
        if not user_piece:
            self.write({'result':False, 'msg':'identity not exists'})
            self.finish()
        ret = cur_room.gobang.addPiece(int(posarr[0]), int(posarr[1]), int(user_piece))
        if not ret.result:
            self.write({'result':False, 'msg':ret.msg})
        else:
            if cur_room.gobang.isGameOver(int(posarr[0]), int(posarr[1])):
                print room_name+u' 游戏结束'
                pubContent([(room_name+'1').encode('UTF-8'), 'end,'+user_piece+','+pos.encode('UTF-8')])
                pubContent([(room_name+'2').encode('UTF-8'), 'end,'+user_piece+','+pos.encode('UTF-8')])
                cur_room.status = GameRoom.STATUS_END
                print u'清空房间'+room_name
                del all_rooms[room_name]
            else:
                pubContent([(room_name+''+user_piece).encode('UTF-8'), pos.encode('UTF-8')])
            self.write({'result':True})


'''
    长连接拿对方下棋位置
'''
class GamePollHandler(web.RequestHandler):

    @tornado.web.asynchronous
    def get(self):
        self.room_name = self.get_argument('room_name')
        self.user_piece = self.get_secure_cookie('up')
        if not self.user_piece:
            self.write({'result':False, 'msg':'user not valid'})
            self.finish()
            return
        self.his_piece = self.user_piece == '1' and '2' or '1'

        topic = (self.room_name+''+self.his_piece).encode('UTF-8')
        print '订阅: '+topic
        ctx = zmq.Context.instance()
        s = ctx.socket(zmq.SUB)
        s.connect(zmq_addr)
        s.setsockopt(zmq.SUBSCRIBE, topic)
        self.stream = zmqstream.ZMQStream(s)

        self.stream.on_recv(self._handle_reply)

    def _handle_reply(self, msg):
        print '接收到消息: '
        print msg
        reply = msg[1]
        self.write({'result':True, 'code':2, 'data':reply}) # code 1:game start, code 2:game step
        self.stream.close()
        self.finish()

    def on_connection_close(self):
        print self.room_name + '' + self.user_piece + u'离线'
        pubContent([(self.room_name+''+self.user_piece).encode('UTF-8'), 'off,'])
        self.stream.stop_on_recv()
        self.stream.close()
        all_rooms[self.room_name].user_piece_ids.remove(int(self.user_piece))
        if not all_rooms[self.room_name].user_piece_ids:
            print u'清空房间'+self.room_name
            del all_rooms[self.room_name]


urls = [
        (r"/room-(.*)", EnterRoomHandler),
        (r"/poll", GamePollHandler),
        (r"/step", GameStepHandler),
        ]

settings = dict(
        template_path = os.path.join(os.path.dirname(__file__), "templates"),
        static_path = os.path.join(os.path.dirname(__file__), "static"),
        cookie_secret = 'werwerwAW15Wwr-wrwe==dssdtfrwerter2t12',
        );

gobang = Gobang()
# room = GameRoom('test')
all_rooms = {}
zmq_addr = 'tcp://127.0.0.1:5005'

ctx = zmq.Context()
zmq_pusher = ctx.socket(zmq.PUB)
zmq_pusher.bind(zmq_addr)

def pubContent(content):
    print content
    zmq_pusher.send_multipart(content)

def main():
    application = web.Application(urls, **settings)

    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
