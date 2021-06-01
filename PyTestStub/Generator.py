
# Copyright (c) 2015-2021 Agalmic Ventures LLC (www.agalmicventures.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import ast, os, astunparse

from PyTestStub import Templates

class ModuleInfo():
	def __init__(self,module):
		self.module = module
		self.imports = []
		self.objs = []

	def add(self,obj):
		self.objs.append(obj)
	
	@property
	def import_str(self):
		return 'from %s import %s'%(self.module,', '.join([o.name for o in self.objs]))

	def get_str(self):
		return Templates.unitTestBase.format(self.import_str) + '\n'.join(o.get_str() for o in self.objs)

class ClassInfo():
	def __init__(self,astobj,includeInternal) -> None:
		self.astobj = astobj
		self.name = astobj.name
		self.methods = []
		self.init = None
		for child in astobj.body:
			if child.name == '__init__':
				self.init = child
			elif (isinstance(child,ast.FunctionDef) and not child.name.startswith('_') or includeInternal):
				method = FuncInfo(child,classmethod=True)
				self.methods.append(method)

	def unparse_class(self):
		if self.init == None:
			return 'cls.obj = %s()'%self.name
		out = astunparse.unparse(self.init).split('\n')
		for l in out:
			if 'def __init__' in l:
				out = l.replace('def __init__','cls.obj = ').replace(':','').replace('self','').replace('(,','(').replace('( ','(').strip()
				break
		return out

	def get_str(self):
		methods_str = '\n'.join(Templates.methodTest.format(m.name,m.constructor) for m in self.methods)
		return Templates.classTest.format(self.name,methods_str,self.unparse_class())

class FuncInfo():
	def __init__(self,astobj,classmethod=False):
		self.astobj = astobj
		self.name = astobj.name
		self.classprefix = 'cls.obj.' if classmethod else ''
		self.constructor = self.unparse_func(astobj)

	def unparse_func(self,astobj):
		out = astunparse.unparse(astobj).split('\n')
		for l in out:
			if 'def ' in l:
				out = l.replace('def ','').replace(':','').replace('self','').replace('(,','(').replace('( ','(').strip()
				break
		return self.classprefix+out

	def get_str(self):
		return Templates.functionTest.format(self.name, self.classprefix+self.constructor)

def generateUnitTest(root, fileName, includeInternal=False):
	"""
	Generates a unit test, given a root directory and a subpath to a file.

	:param root: str
	:param fileName: str
	:return: str or None
	"""
	#Skip non-Python files
	if not fileName.endswith('.py'):
		return None

	#Skip symlinks
	path = os.path.join(root, fileName)
	if os.path.islink(path):
		print('Symlink: %s' % path)
		return None

	#Get the parts of the filename
	pathParts = os.path.split(path)
	fileName = pathParts[-1]
	module, _ = os.path.splitext(fileName)
	moduleObj = ModuleInfo(module)

	#Load the file
	try:
		text = open(path).read()
	except UnicodeDecodeError as ude:
		print('Unicode decode error for %s: %s' % (path, ude))
		return None

	#Parse it
	try:
		tree = ast.parse(text)
	except Exception as e: #@suppress warnings since this really does need to catch all
		print('Failed to parse %s' % path)
		print(e)
		return None

	#Walk the AST
	for node in [n for n in tree.body if (not n.name.startswith('_') or includeInternal)]:
		if isinstance(node,ast.ClassDef):
			moduleObj.add(ClassInfo(node,includeInternal))

		elif isinstance(node,ast.FunctionDef):
			moduleObj.add(FuncInfo(node))

	if len(moduleObj.objs) == 0:
		print('No classes or functions in %s' % path)
		return None
	else:
		return moduleObj.get_str()