'''
Created on 2015年1月4日

@author: tanbro
'''

class Foo:
    
    @classmethod
    def echo(cls, txt):
        return '{}::echo({})'.format(cls, txt)
        