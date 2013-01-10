#!/bin/env python
# encoding=utf-8

#用apt-get install python-tornado安装的不是最新，有bug。要用 pip install tornado
#
#此方案采用websocket实现

import os
from Gobang import Gobang, GameRoom
import random

import tornado
import json
from tornado import web, autoreload, websocket, ioloop
from Config import Config
from datetime import timedelta

'''
    进入房间页面
'''
class EnterRoomHandler(web.RequestHandler):

    def get(self, room_name):

        if not room_name in GameSocketHandler.all_rooms.keys(): #新房间
            piece_id = random.randint(1,2)
            room = GameRoom(room_name, piece_id)
            self.render('index.html', cur_room=room, my_piece_id=piece_id, is_waiting=True,
                all_rooms_count=len(GameSocketHandler.all_rooms)+1,
                config=Config,
                )
        else:
            if len(GameSocketHandler.all_rooms[room_name].user_piece_ids) == 2: #已经满了
                readonly = True
                if isLog:  print '房间已被占用'
                self.render('msg.html', msg="房间已被占用", config=Config,
                    all_rooms_count = len(GameSocketHandler.all_rooms),)
                return
            elif len(GameSocketHandler.all_rooms[room_name].user_piece_ids) == 1:
                if isLog:  print '游戏开始'
                his_piece_id = 1 in GameSocketHandler.all_rooms[room_name].user_piece_ids and 1 or 2
                my_piece_id = his_piece_id == 1 and 2 or 1
                hiskey = room_name+'-'+str(his_piece_id)
                GameSocketHandler.all_rooms[room_name].user_piece_ids.add(my_piece_id)

                GameSocketHandler.all_rooms[room_name].status = GameRoom.STATUS_GOING
                topic = (room_name+''+str(my_piece_id)).encode('UTF-8')
                ioloop.IOLoop.instance().add_timeout(timedelta(seconds=1), self._writemsg_callback(hiskey) )
                self.render('index.html', cur_room=GameSocketHandler.all_rooms[room_name],
                    my_piece_id = my_piece_id,
                    is_waiting = (my_piece_id==2),
                    all_rooms_count = len(GameSocketHandler.all_rooms),
                    config = Config,
                    )

    def _writemsg_callback(self, hiskey):
         if hiskey in GameSocketHandler.socket_handlers:
            GameSocketHandler.socket_handlers[hiskey].write_message({'type':'on_gamestart'})


'''
    用websocket来与前端通信
'''
class GameSocketHandler(tornado.websocket.WebSocketHandler):

    socket_handlers = {}   #房间名-1:GameSocketHandler 一个房间每个人有一个值, 1用户订阅 room-1
    all_rooms = {}  # 房间名:GameRoom
    active_timeout = 60000 # 超时时间，超时后关闭房间

    def open(self):

        self.room_name = self.get_argument('room')
        self.user_piece = int(self.get_argument('up'))
        self.his_piece = self.user_piece == 1 and 2 or 1
        self.room_name = self.room_name.encode('utf-8')
        self.mykey = "%s-%d" % (self.room_name, self.user_piece)
        self.hiskey = "%s-%d" % (self.room_name, self.his_piece)
        self.is_active = False  #标志是否有活动，是否有人下棋，时间太长没人动，就关闭房间

        if not self.room_name in GameSocketHandler.all_rooms:  #第一次进入房间
            room = GameRoom(self.room_name, self.user_piece)
            GameSocketHandler.all_rooms[self.room_name] = room
            if isLog:  print '第一个进入'

        if isLog: print "User %d has entered the room: %s" % (self.user_piece, self.room_name)
        if not self.mykey in GameSocketHandler.socket_handlers:
            GameSocketHandler.socket_handlers[self.mykey] = self
        self.write_message({'type':'online'})

        chek_active = tornado.ioloop.PeriodicCallback(self._check_active_callback, GameSocketHandler.active_timeout)
        chek_active.start()
        return

    def on_close(self):   ##还有问题，刷新的时候
        GameSocketHandler.all_rooms[self.room_name].user_piece_ids.remove(self.user_piece)
        if isLog: print 'User %d  has left the room: %s' % (self.user_piece, self.room_name)

        del GameSocketHandler.socket_handlers[self.mykey]

        if not GameSocketHandler.all_rooms[self.room_name].user_piece_ids:  #房间没人了
            if isLog: print '移除房间: %s' % self.room_name
            del GameSocketHandler.all_rooms[self.room_name]
        else: #房间还有一个人，向这个人发通知
            if not GameSocketHandler.socket_handlers:
                return
            if isLog: print 'Let the other guy know i\'m leaving.'
            socket = GameSocketHandler.socket_handlers[self.hiskey]
            # 给对方发
            ioloop.IOLoop.instance().add_timeout(timedelta(seconds=1),
                    lambda:socket.write_message({'type':'offline'}) )
            
            GameSocketHandler.all_rooms[self.room_name].gobang.pieces = [([0] * (Gobang.GRID_SIZE+1)) for i in range(Gobang.GRID_SIZE+1)]
            GameSocketHandler.all_rooms[self.room_name].gobang.last_piece = None
            GameSocketHandler.all_rooms[self.room_name].status = GameRoom.STATUS_WAITING

        return

    def on_message(self, message):
        self.is_active = True
        if isLog: print 'Room '+self.room_name+' websocket receive message: ' + message
        msg = json.loads(message)
        if not 'type' in msg:
            print 'Error. message has no type filed.'
            return
        self._gamemove(msg)
        return

    def allow_draft76(self):
        return True

    def _gamemove(self, msg):
        self.is_active = True
        row = msg.get(u'row')
        col = msg.get(u'col')
        room = GameSocketHandler.all_rooms[self.room_name]
        ret = room.gobang.addPiece(row, col, self.user_piece)
        if not ret.result:
            return False
        else:
            if room.gobang.isGameOver(row, col):  #游戏结束
                if isLog:  print "Room: %s gameover." % self.room_name.encode('UTF-8')
                socket = GameSocketHandler.socket_handlers[self.hiskey]
                socket.write_message({'type':'on_gameover'})
                self.write_message({'type':'on_gameover'})
                self.close()
                socket.close()
            else:
                socket = GameSocketHandler.socket_handlers[self.hiskey]
                socket.write_message({'type':'on_gamemove', 'row':row, 'col':col})
        return True

    def _check_active_callback(self):
        if not self.is_active:
            if isLog:  print '超时移除房间: %s' % self.room_name
            self.close()

class RoomListHandler(web.RequestHandler):

    def get(self):
        self.render('rooms.html',
                    all_rooms_count = len(GameSocketHandler.all_rooms),
                    config = Config,
                    rooms = GameSocketHandler.all_rooms,
                    )


urls = [
        (r"/room-(.{1,200})", EnterRoomHandler),
        (r"/rooms", RoomListHandler),
        (r"/", RoomListHandler),
        (r"/gamesocket", GameSocketHandler),
        ]

settings = dict(
        template_path = os.path.join(os.path.dirname(__file__), "templates"),
        static_path = os.path.join(os.path.dirname(__file__), "static"),
        cookie_secret = 'werwerwAW15Wwr-wrwe==dssdtfrwerter2t12',
        );

isLog = True

def main():
    application = web.Application(urls, **settings)

    application.listen(8888)
    # tornado.autoreload.start(tornado.ioloop.IOLoop.instance()) # add this to enable autorestart
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
