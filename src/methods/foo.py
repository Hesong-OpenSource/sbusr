# -*- coding: utf-8 -*-

class Foo:
    
    @classmethod
    def echo(cls, txt):
        return '{}::echo({})'.format(cls, txt)
        