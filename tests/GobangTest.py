import sys
sys.path.insert(0, '../')
from Gobang import Gobang
import unittest

class GobangTestCase(unittest.TestCase):

	def setUp(self):
		pass

	def test_gobang(self):
		gobang = Gobang()
		self.assertIsNotNone(gobang.pieces)
		ret = gobang.addPiece(2,2,1)
		self.assertTrue(ret.result)
		self.assertEqual(gobang.pieces[2][2], 1)

		ret = gobang.addPiece(2,8,1)		
		self.assertFalse(ret.result)

		ret = gobang.addPiece(2,2,2)		
		self.assertFalse(ret.result)

	def test_isGameOver(self):
		gobang = Gobang()
		gobang.addPiece(0,0,1)
		gobang.addPiece(0,1,2)
		gobang.addPiece(1,0,1)
		gobang.addPiece(1,1,2)
		gobang.addPiece(2,0,1)
		gobang.addPiece(2,1,2)
		gobang.addPiece(3,0,1)
		gobang.addPiece(3,1,2)
		gobang.addPiece(4,0,1)
		gobang.addPiece(4,1,2)
		
		self.assertTrue(gobang.isGameOver(4,0))

if __name__ == '__main__':
	unittest.main()
