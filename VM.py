import re
from Node import BasicExecutionNode, InputNode, OutputNode
from Enums import *

class VM(object):
    def __init__(self):
        self.nodes = []
        self.inputs = []
        self.outputs = []

    def create_nodes(self):
        self.nodes = []
        for i in range(12):
            node = BasicExecutionNode(i)
            self.nodes.append(node)

        self.connect_nodes()
        self.set_inputs()
        self.set_outputs()

    def set_inputs(self):
        input_node = InputNode(0)
        self.inputs.append(input_node)
        input_node.connect(self.nodes[1], PORT_DOWN)
        #input_node.values = [1, 42, 50, 2, 10, -1, -999]
        input_node.values = [66, 34, 88, 91, 53, 96, 47,
                             68, 83, 59, 58, 56, 15, 81,
                             18, 95, 44, 72, 66, 14, 81,
                             43, 45, 23, 72, 33, 23, 29,
                             30, 58, 75, 44, 62, 38, 60,
                             82, 24, 52]


    def set_outputs(self):
        pass
        output_node = OutputNode(0)
        self.outputs.append(output_node)
        output_node.connect(self.nodes[10], PORT_UP)
        output_node.len_objective = len(self.inputs[0].values)

    def split_sourcecode(self, fn):
        f = open(fn, 'r')
        lines = f.read().splitlines()
        f.close()
        print "split_sourcecode lines:", lines

        i = 0
        node_id = -1
        defined_nodes_index = []
        for line in lines:
            word = re.match(r'@(\d+)', line)
            if word is not None:
                defined_nodes_index.append(node_id)
                node_id = int(word.group(1))
                if node_id in defined_nodes_index:
                    raise Exception("Can't have the same node multiple times : @%i is already defined" % node_id)
                i = 0
            elif i < 15 and len(self.nodes) > 0:
                self.nodes[node_id].add_source_line(line)
                #self.nodes[-1].parse(node_code_lines[:])
            i += 1
        print "split_sourcecode nodes:"
        for node in self.nodes:
            print node.id, node.source_code

    def parse(self):
        '''Distributed parsing'''
        for node in self.nodes:
            node.parse()

    def connect_nodes(self):
        for row in range(HEIGHT):
            for col in range(WIDTH):
                node = self.nodes[WIDTH * row + col]

                if row > 0 and row < HEIGHT:
                    other = self.nodes[WIDTH * (row - 1) + col]
                    node.connect(other, PORT_UP)

                if col > 0 and col < WIDTH:
                    other = self.nodes[WIDTH * row + (col - 1)]
                    node.connect(other, PORT_LEFT)

        for row in range(HEIGHT):
            for col in range(WIDTH):
                node = self.nodes[WIDTH * row + col]
                print node.id, node.neighbors

    def run(self):
        for node in self.nodes:
            node.first_pass()

        # for i in range(20):
        i = 1
        while True:
            for node in self.inputs:
                node.before_cycle()
            for node in self.nodes:
                node.before_cycle()
            for node in self.outputs:
                node.before_cycle()

            print "-- cycle", i+1
            for node in self.inputs:
                node.cycle()
            for node in self.nodes:
                node.cycle()
            for node in self.outputs:
                node.cycle()

            for node in self.inputs:
                node.after_cycle()
            for node in self.nodes:
                node.after_cycle()
                if len(node.instr) > 0:
                    print '[', node.id, ']', node.ip, node.state, ':', node.fetch(), node.regs
            for node in self.outputs:
                node.after_cycle()

            # exit
            # for node in self.inputs:
            #     if node.end_reached is True:
            #         return
            for node in self.nodes:
                if node.halted is True:
                    return
            for node in self.outputs:
                if len(node.values) == node.len_objective:
                    return
            self.compare_io()
            i += 1

    def compare_io(self):
        for i, o in map(None, self.inputs, self.outputs):
            for ival, oval in map(None, i.values, o.values):
                print "|", ival, "|", oval, "|"