from . import interface

class IFCN(interface.IExternalSource):
    def update(self):
        print('OH I\'m updated!!!!')