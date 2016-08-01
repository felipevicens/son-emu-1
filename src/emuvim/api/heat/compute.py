from resources import *


class HeatCompute:
    def __init__(self):
        self.dcs = dict()
        self.stacks = dict()

    def add_stack(self, stack):
        self.stacks[stack.id] = stack
