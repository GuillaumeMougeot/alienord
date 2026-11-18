import unittest

class TestExample(unittest.TestCase):

    @unittest.skip("example test")
    def test_(self):
        pass

if __name__ == '__main__':
    unittest.main()