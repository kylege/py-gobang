#encoding=utf-8
class BasicReturn():

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
		self.pieces = [([0] * (self.GRID_SIZE+1)) for i in range(self.GRID_SIZE+1)]

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

	'''
		the game is over or not 
		return bool
	'''
	def isGameOver(self, row, col):
		rlen = self.GRID_SIZE+1;
		alldirecs = []
		gv = self.pieces[row][col]

		onedirec = [gv]
		for i in range(1,5): #横向
			if col-i in range(0, rlen): onedirec.insert(0, self.pieces[row][col-i])
		for i in range(1,5):
			if col+i in range(0, rlen): onedirec.append(self.pieces[row][col+i])
		alldirecs.append(onedirec)

		onedirec = [gv]
		for i in range(1,5): #竖向
			if row-i in range(0, rlen): onedirec.insert(0, self.pieces[row-i][col])
		for i in range(1,5):
			if row+i in range(0, rlen): onedirec.append(self.pieces[row+i][col])
		alldirecs.append(onedirec)

		onedirec = [gv]
		for i in range(1,5): #/向
			if col+i in range(0, rlen) and row-i in range(0, rlen): onedirec.insert(0, self.pieces[row-i][col+i])
		for i in range(1,5):
			if col-i in range(0, rlen) and row+i in range(0, rlen): onedirec.append(self.pieces[row+i][col-i])
		alldirecs.append(onedirec)

		onedirec = [gv]
		for i in range(1,5): #\向
			if col-i in range(0, rlen) and row-i in range(0, rlen): onedirec.insert(0, self.pieces[row-i][col-i])
		for i in range(1,5):
			if col+i in range(0, rlen) and row+i in range(0, rlen): onedirec.append(self.pieces[row+i][col+i])
		alldirecs.append(onedirec)

		#找是否存在五个连续值
		for direc in alldirecs:
			fst = None
			count = 0
			for g in direc:
				if g == gv and not fst:
					count = 1
					fst = True
				elif g == gv and fst:
					count = count+1
				elif not g== gv and fst:
					break
			if count >= 5:
				return True

		return False


class GameRoom():
	STATUS_WAITING = 0;
	STATUS_GOING   = 1
	STATUS_END     = 2

	def __init__(self, room_name, piece_id):
		self.gobang = Gobang()
		self.status = self.STATUS_WAITING
		self.room_name = room_name
		self.user_piece_ids = set([piece_id])
