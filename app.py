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
        rn = self.get_secure_cookie('rn')
        up = self.get_secure_cookie('up')
        if rn and up:
            removeUserFromRoom(rn, [int(up)])  #将以前那个房间移除本用户

        if not room_name in all_rooms.keys(): #新房间
            piece_id = random.randint(1,2)
            self.set_secure_cookie('up', str(piece_id))  #棋子颜色号，你是黑棋还是白棋，随机分配
            self.set_secure_cookie('rn', room_name) #房间名称

            room = GameRoom(room_name, piece_id)
            all_rooms[room_name] = room
            self.render('index.html', cur_room=room, my_piece_id=piece_id, is_waiting=True,
                all_rooms_count=len(all_rooms),
                )
            if isLog:  print u'第一个进入'
        else:
            if len(all_rooms[room_name].user_piece_ids) == 2: #已经满了
                readonly = True
                self.write('房间已被占用')
                if isLog:  print '房间已被占用'
            elif len(all_rooms[room_name].user_piece_ids) == 1:
                my_piece_id = 1 in all_rooms[room_name].user_piece_ids and 2 or 1
                all_rooms[room_name].user_piece_ids.add(my_piece_id)
                self.set_secure_cookie('up', str(my_piece_id))
                self.set_secure_cookie('rn', room_name)

                all_rooms[room_name].status = GameRoom.STATUS_GOING
                topic = (room_name+''+str(my_piece_id)).encode('UTF-8')
                pubContent([topic,'start,'])
                self.render('index.html', cur_room=all_rooms[room_name], my_piece_id=my_piece_id, is_waiting=(my_piece_id==2), 
                    all_rooms_count=len(all_rooms),
                    )
                if isLog:  print '游戏开始'

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

        room_name = self.get_secure_cookie('rn')
        if not room_name in all_rooms.keys(): 
            self.write({'result':False, 'msg':'room not exists'})
            self.finish()
        if not all_rooms[room_name].status == GameRoom.STATUS_GOING:
            self.write({'result':False, 'msg':'room not going'})
            self.finish()
        user_piece = self.get_secure_cookie('up')
        if not user_piece:
            self.write({'result':False, 'msg':'identity not exists'})
            self.finish()

        ret = all_rooms[room_name].gobang.addPiece(int(posarr[0]), int(posarr[1]), int(user_piece))
        if not ret.result:
            self.write({'result':False, 'msg':ret.msg})
        else:
            if all_rooms[room_name].gobang.isGameOver(int(posarr[0]), int(posarr[1])):
                if isLog:  print room_name+u' 游戏结束'
                pubContent([(room_name+'1').encode('UTF-8'), 'end,'+user_piece+','+pos.encode('UTF-8')])
                pubContent([(room_name+'2').encode('UTF-8'), 'end,'+user_piece+','+pos.encode('UTF-8')])
                all_rooms[room_name].status = GameRoom.STATUS_END
                if isLog:  print u'清空房间'+room_name
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
        self.room_name = self.get_secure_cookie('rn')
        self.user_piece = self.get_secure_cookie('up')
        if not self.user_piece or not self.room_name:
            self.write({'result':False, 'msg':'user not valid'})
            self.finish()
            return
        self.his_piece = self.user_piece == '1' and '2' or '1'

        topic = (self.room_name+''+self.his_piece).encode('UTF-8')
        if isLog:  print u'订阅: '+topic
        ctx = zmq.Context.instance()
        s = ctx.socket(zmq.SUB)
        s.connect(zmq_addr)
        s.setsockopt(zmq.SUBSCRIBE, topic)
        self.stream = zmqstream.ZMQStream(s)

        self.stream.on_recv(self._handle_reply)

    def _handle_reply(self, msg):
        reply = msg[1]
        self.write({'result':True, 'code':2, 'data':reply}) # code 1:game start, code 2:game step
        self.stream.close()
        self.finish()

    def on_connection_close(self):
        if isLog:  print self.room_name + '' + self.user_piece + u'离线'
        pubContent([(self.room_name+''+self.user_piece).encode('UTF-8'), 'off,'])
        self.stream.stop_on_recv()
        self.stream.close()
        try:
            removeUserFromRoom(self.room_name, [int(self.user_piece)])
            if not all_rooms[self.room_name].user_piece_ids:
                del all_rooms[self.room_name]
        except:
            pass

class GameAliveHandler(web.RequestHandler):

    @web.asynchronous
    def get(self):
        self.room_name = self.get_secure_cookie('rn')
        self.user_piece = self.get_secure_cookie('up')
        if not self.room_name or not self.user_piece:
            self.finish()

    def on_connection_close(self):
        print 'Alive连接断开'
        try:
            removeUserFromRoom(self.room_name, [int(self.user_piece)])
        except:
            pass

'''
    移除指定房间指定用户
'''
def removeUserFromRoom(room_name, user_pieces):
    if not room_name in all_rooms.keys():
        return False
    if isLog: print '移除用户:'+','.join([str(u) for u in user_pieces])
    for piece in user_pieces:
        if piece in all_rooms[room_name].user_piece_ids:
            all_rooms[room_name].user_piece_ids.remove(piece)
    all_rooms[room_name].gobang.pieces = [([0] * (Gobang.GRID_SIZE+1)) for i in range(Gobang.GRID_SIZE+1)]
    all_rooms[room_name].gobang.last_piece = None
    if not all_rooms[room_name].user_piece_ids:
            del all_rooms[room_name]
    return True


urls = [
        (r"/room-(.*)", EnterRoomHandler),
        (r"/poll", GamePollHandler),
        (r"/step", GameStepHandler),
        (r"/alive", GameAliveHandler),
        ]

settings = dict(
        template_path = os.path.join(os.path.dirname(__file__), "templates"),
        static_path = os.path.join(os.path.dirname(__file__), "static"),
        cookie_secret = 'werwerwAW15Wwr-wrwe==dssdtfrwerter2t12',
        );

isLog = False
gobang = Gobang()
# room = GameRoom('test')
all_rooms = {}
zmq_addr = 'tcp://127.0.0.1:5005'

ctx = zmq.Context()
zmq_pusher = ctx.socket(zmq.PUB)
zmq_pusher.bind(zmq_addr)

def pubContent(content):
    # print content
    zmq_pusher.send_multipart(content)

def main():
    application = web.Application(urls, **settings)

    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
