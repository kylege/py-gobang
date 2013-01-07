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

if __name__ == '__main__':
	unittest.main()
