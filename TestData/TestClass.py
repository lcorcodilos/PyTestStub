class TestClass(object):

	def methodA(self, x, y):
		pass

	def methodB(self):
		pass

	def _internalMethod(self, q, r):
		pass

class TestClass2(object):
	def methodA(self, x, y):
		pass

	def methodB(self):
		raise ValueError("This breaks deliberately.")

	def _internalMethod(self, q, r):
		pass

def func_test_one():
	pass

def func_test_two():
	pass

def func_test_raise(x,y):
	if not isinstance(x,float):
		raise TypeError("This is the wrong type")
	
	if x+y > 0:
		raise ValueError("This breaks deliberately.")
	else:
		return True
	