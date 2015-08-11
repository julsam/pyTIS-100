import re
from Node import BasicExecutionNode, InputNode, OutputNode
from Enums import *

class VM(object):
    def __init__(self):
        self.nodes = []
        self.input_nodes = []
        self.output_nodes = []
        self.input_values = []
        self.output_values = []

    def create_nodes(self):
        self.nodes = []
        for i in range(12):
            node = BasicExecutionNode(i)
            self.nodes.append(node)

        self.connect_nodes()
        self.create_input_nodes()
        self.create_output_nodes()

    def create_input_nodes(self):
        for i, input_vals in enumerate(self.input_values):
            if input_vals is not None:
                node = InputNode(i)
                node.values = input_vals[:]
                node.connect(self.nodes[i], PORT_DOWN)
                self.input_nodes.append(node)

    def create_output_nodes(self):
        for i, output_vals in enumerate(self.output_values):
            if output_vals is not None:
                node = OutputNode(i)
                node.values = output_vals[:]
                pos = WIDTH * (HEIGHT - 1) + i
                node.connect(self.nodes[pos], PORT_UP)
                node.len_objective = len(self.input_nodes[0].values)
                self.output_nodes.append(node)

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

    def load(self, tis_filename):
        import os, imp
        if os.path.exists(tis_filename):
            dir_name = os.path.dirname(tis_filename)
            basename, extension = os.path.splitext(os.path.basename(tis_filename))
            test_filename = dir_name + '/' + basename + '.py'
            if os.path.exists(test_filename):
                mod = imp.load_source(basename, test_filename)
                self.add_input_list(mod, ['TIS_IN_0', 'TIS_IN_1', 'TIS_IN_2', 'TIS_IN_3'])
                self.add_output_list(mod, ['TIS_OUT_0', 'TIS_OUT_1', 'TIS_OUT_2', 'TIS_OUT_3'])

            self.create_nodes()
            self.split_sourcecode(tis_filename)
            self.parse()

    def add_input_list(self, mod, lst):
        for i in lst:
            if hasattr(mod, i):
                self.input_values.append(getattr(mod, i))
            else:
                self.input_values.append(None)

    def add_output_list(self, mod, lst):
        for i in lst:
            if hasattr(mod, i):
                self.output_values.append(getattr(mod, i))
            else:
                self.output_values.append(None)

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
            for node in self.input_nodes:
                node.before_cycle()
            for node in self.nodes:
                node.before_cycle()
            for node in self.output_nodes:
                node.before_cycle()

            print "-- cycle", i
            for node in self.input_nodes:
                node.cycle()
            for node in self.nodes:
                node.cycle()
            for node in self.output_nodes:
                node.cycle()

            for node in self.input_nodes:
                node.after_cycle()
            for node in self.nodes:
                node.after_cycle()
                if len(node.instr) > 0:
                    print '[', node.id, ']', node.ip, node.state, ':', node.fetch(), node.regs
            for node in self.output_nodes:
                node.after_cycle()

            # exit
            # for node in self.input_nodes:
            #     if node.end_reached is True:
            #         return
            for node in self.nodes:
                if node.halted is True:
                    return
            for node in self.output_nodes:
                if len(node.values) == node.len_objective:
                    return
            #self.compare_io()
            i += 1

    def compare_io(self):
        for i, o in map(None, self.input_nodes, self.output_nodes):
            if i is not None and o is not None:
                for ival, oval in map(None, i.values, o.values):
                    print "|", ival, "|", oval, "|"