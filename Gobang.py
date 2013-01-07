#encoding=utf-8
class BasicReturn():
	result = True
	code   = 0
	msg    = ''
	data   = None

	def __init__(self, result=True, code=0, msg='', data=None):
		self.result = result
		self.code = code
		self.msg = msg
		self.data = data


class Gobang():
	GRID_SIZE   = 15	
	PIECE_NONE  = 0
	PIECE_BLACK = 1
	PIECE_WHITE = 2

	last_piece = None #上次下的是黑方还是白方

	def __init__(self):
		self.pieces = [[0] * self.GRID_SIZE] * self.GRID_SIZE

	'''
		row and col start with 0
	'''
	def addPiece(self, row, col, value):
		if not self.pieces[row][col] == 0:
			return BasicReturn(False, -1, '该位置已存在棋子。')
		if self.last_piece and self.last_piece == value:
			return BasicReturn(False, -2, '对方还没有下子。')
		self.pieces[row][col] = value 
		self.last_piece = value
		return BasicReturn()

class GameRoom():
	STATUS_WAITING = 0;
	STATUS_GOING   = 1
	STATUS_END     = 2

	def __init__(self, room_name, piece_id):
		self.gobang = Gobang()
		self.status = self.STATUS_WAITING
		self.room_name = room_name
		self.user_piece_ids = set(piece_id)
