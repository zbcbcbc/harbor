#setup.py

from distutils.core import setup, Extension

example_mod = Extension('hello', sources = ['hello.c'])
setup(name = "hello", version = "0.1", 
		description = "first extension module", 
			ext_modules = [example_mod])

