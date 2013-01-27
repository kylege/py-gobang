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
import logging
from tornado.options import define, options  

define("port", default=8888, help="Run server on a specific port", type=int)  

'''
    进入房间页面
'''
class EnterRoomHandler(web.RequestHandler):

    def get(self, room_name):

        if not room_name in GameSocketHandler.all_rooms: #新房间
            piece_id = random.randint(1,2)
            room = GameRoom(room_name, piece_id)
            self.render('index.html', cur_room=room, my_piece_id=piece_id, is_waiting=True,
                all_rooms_count=len(GameSocketHandler.all_rooms)+1,
                config=Config,
                )
        else:
            if len(GameSocketHandler.all_rooms[room_name].user_piece_ids) == 2: #已经满了
                readonly = True
                if isLog:  logging.info('房间已被占用')
                self.render('msg.html', msg="房间已被占用", config=Config,
                    all_rooms_count = len(GameSocketHandler.all_rooms),)
                return
            elif len(GameSocketHandler.all_rooms[room_name].user_piece_ids) == 1:
                his_piece_id = 1 in GameSocketHandler.all_rooms[room_name].user_piece_ids and 1 or 2
                my_piece_id = his_piece_id == 1 and 2 or 1

                self.render('index.html', cur_room=GameSocketHandler.all_rooms[room_name],
                    my_piece_id = my_piece_id,
                    is_waiting = (my_piece_id==2),
                    all_rooms_count = len(GameSocketHandler.all_rooms),
                    config = Config,
                    )
            else:
                logging.info( 'room user_piece_ids is empty.')



'''
    用websocket来与前端通信
'''
class GameSocketHandler(tornado.websocket.WebSocketHandler):

    socket_handlers = {}   #房间名-1:GameSocketHandler 一个房间每个人有一个值, 1用户订阅 room-1
    all_rooms = {}  # 房间名:GameRoom
    active_timeout = 600000 # 超时时间，超时后关闭房间

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
            if isLog: logging.info('第一个进入')

        if isLog: logging.info( "User %d has entered the room: %s" % (self.user_piece, self.room_name) )
        if not self.mykey in GameSocketHandler.socket_handlers:
            GameSocketHandler.socket_handlers[self.mykey] = self

        GameSocketHandler.all_rooms[self.room_name].user_piece_ids.add(self.user_piece)

        if self.hiskey in GameSocketHandler.socket_handlers: #对方也在线，游戏开始
            if isLog:  logging.info( '游戏开始')
            GameSocketHandler.socket_handlers[self.hiskey].write_message({'type':'on_gamestart'})
            self.write_message({'type':'on_gamestart'})
            GameSocketHandler.all_rooms[self.room_name].status = GameRoom.STATUS_GOING

        self.chek_active = tornado.ioloop.PeriodicCallback(self._check_active_callback, GameSocketHandler.active_timeout)
        self.chek_active.start()
        return

    def on_close(self):
        try:   
            GameSocketHandler.all_rooms[self.room_name].user_piece_ids.remove(self.user_piece)
            if isLog: logging.info( 'User %d  has left the room: %s' % (self.user_piece, self.room_name) )

            if not GameSocketHandler.all_rooms[self.room_name].user_piece_ids:  #房间没人了
                if isLog: logging.info( '移除房间: %s' % self.room_name )
                del GameSocketHandler.all_rooms[self.room_name]
            else: #房间还有一个人，向这个人发通知
                if isLog: logging.info( 'Let the other guy know i\'m leaving.' )
                try:
                    socket = GameSocketHandler.socket_handlers[self.hiskey]
                    # 给对方发
                    socket.write_message({'type':'offline'})
                    GameSocketHandler.all_rooms[self.room_name].gobang.pieces = [([0] * (Gobang.GRID_SIZE+1)) for i in range(Gobang.GRID_SIZE+1)]
                    GameSocketHandler.all_rooms[self.room_name].gobang.last_piece = None
                    GameSocketHandler.all_rooms[self.room_name].status = GameRoom.STATUS_WAITING        
                except:
                    logging.error( '_onclose_callback Exception.' )
                    pass
        except:
            logging.error( 'on_close Exception.' )

        if self.mykey in GameSocketHandler.socket_handlers:
            del GameSocketHandler.socket_handlers[self.mykey]
        self.chek_active.stop()
        return True

    def on_message(self, message):
        self.is_active = True
        if isLog: logging.info( 'Room '+self.room_name+' websocket receive message: ' + message )
        msg = json.loads(message)
        if not 'type' in msg:
            logging.error( 'Error. message has no type filed.')
            return
        msgtype = msg.get(u'type')
        if msgtype == 'on_gamemove':
            self._on_gamemove(msg)
        elif msgtype == 'on_chat':
            self._on_chat(msg)
        return

    def allow_draft76(self):
        return True

    def _on_chat(self, msg):
        if not self.hiskey in GameSocketHandler.socket_handlers:
            return False
        socket = GameSocketHandler.socket_handlers[self.hiskey]
        content = msg.get(u'content', '')
        if not content:
            return False
        socket.write_message({'type':'on_chat', 'content':content})
        return True

    def _on_gamemove(self, msg):
        self.is_active = True
        row = msg.get(u'row')
        col = msg.get(u'col')
        room = GameSocketHandler.all_rooms[self.room_name]
        ret = room.gobang.addPiece(row, col, self.user_piece)
        if not ret.result:
            return False
        else:
            socket = GameSocketHandler.socket_handlers[self.hiskey]
            socket.write_message({'type':'on_gamemove', 'row':row, 'col':col})
            if room.gobang.isGameOver(row, col):  #游戏结束
                if isLog:  logging.info( "Room: %s gameover." % self.room_name.encode('UTF-8') )
                socket = GameSocketHandler.socket_handlers[self.hiskey]
                socket.write_message({'type':'on_gameover'})
                self.write_message({'type':'on_gameover'})
                self.close()
                socket.close()
        return True

    def _check_active_callback(self):
        if not self.is_active:
            if isLog:  logging.info( '超时移除房间: %s' % self.room_name )
            try:
                self.close()
            except:
                pass

class RoomListHandler(web.RequestHandler):

    def get(self):
        self.render('rooms.html',
                    all_rooms_count = len(GameSocketHandler.all_rooms),
                    config = Config,
                    rooms = GameSocketHandler.all_rooms,
                    )


def printAllRooms():
    logging.info( 'All rooms: ' )
    logging.info( GameSocketHandler.all_rooms)
    logging.info( 'All handlers: ')
    logging.info( GameSocketHandler.socket_handlers)

urls = [
        (r"/room-(.{1,200})", EnterRoomHandler),
        (r"/rooms", RoomListHandler),
        (r"/", RoomListHandler),
        (r"/gs", GameSocketHandler),
        ]

settings = dict(
        template_path = os.path.join(os.path.dirname(__file__), "templates"),
        static_path = os.path.join(os.path.dirname(__file__), "static"),
        cookie_secret = 'werwerwAW15Wwr-wrwe==dssdtfrwerter2t12',
        );

isLog = True

def main():
    # printrooms = tornado.ioloop.PeriodicCallback(printAllRooms, GameSocketHandler.active_timeout)
    # printrooms.start()
    tornado.options.parse_command_line() # -log_file_prefix=your complete path/test_log@8091.log
    application = web.Application(urls, **settings)
    application.listen(options.port)
    # tornado.autoreload.start(tornado.ioloop.IOLoop.instance()) # add this to enable autorestart
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
