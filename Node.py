from Parser import Parser
from SymbolTable import SymbolTable
from Utils import clamp
from Enums import *

class IONode(object):
    def __init__(self):
        pass

class ParserNode(object):
    def __init__(self):
        self.source_code = []
        self.symtable = SymbolTable()
        self.instr = []
        self.parser = Parser(self.symtable, self.instr)

    def parse(self, code_lines=None):
        if code_lines is None:
            code_lines = self.source_code
        code = '\n'.join(code_lines)
        self.parser.parse(code)

    def add_source_line(self, line):
        self.source_code.append(line)


class BasicNode(ParserNode):
    def __init__(self, _id=None):
        super(BasicNode, self).__init__()
        self.id = _id
        self.ip = 0
        self.halted = False

        self.ports = []
        self.read_locked = False # can the neighbor node read from this node ? set to false after each cycle ending
        self.neighbors = {}
        self.blocked = False
        self.state = NODE_STATE_IDLE

        self.deadlock = False

        self.cycle_count = 0

    def fetch(self):
        if len(self.instr) > 0:
            return self.instr[self.ip]

    def fetch_next(self):
        raise NotImplemented

    def __repr__(self):
        return "BasicNode %i %s\n" % (self.id, self.instr)

    @staticmethod
    def opposite_dir(dir):
        assert dir in PORTS_LIST
        if   dir == PORT_LEFT:  return PORT_RIGHT
        elif dir == PORT_RIGHT: return PORT_LEFT
        elif dir == PORT_UP:    return PORT_DOWN
        elif dir == PORT_DOWN:  return PORT_UP

    def connect(self, other, direction):
        self.neighbors[direction] = other
        other.neighbors[self.opposite_dir(direction)] = self


class BasicExecutionNode(BasicNode):
    def __init__(self, _id=None):
        super(BasicExecutionNode, self).__init__(_id)
        self.regs = { REG_ACC: 0, REG_BAK: 0, REG_NIL: 0,
                      REG_LEFT: None, REG_RIGHT: None, REG_UP: None, REG_DOWN: None,
                      REG_ANY: None, REG_LAST: None }

    def __repr__(self):
        return "ExecutionNode %i %s\n" % (self.id, self.instr)

    def run(self):
        if len(self.instr) < 1:
            return
        while not self.halted:
            self.cycle()

    def first_pass(self):
        new_instr = []
        for index, instr in enumerate(self.instr):
            if instr.type == INSTR_LABEL:
                addr = len(new_instr)
                self.symtable.add(instr.value, addr)
            else:
                new_instr.append(instr)

            # errors checks
            if instr.src_type == SRC_TYPE_INT:
                if instr.src < INT_MIN:
                    raise Exception('Value below %i' % INT_MIN)
                if instr.src > INT_MAX:
                    raise Exception('Value over %i' % INT_MAX)

        self.instr = new_instr[:]

    def fetch_next(self):
        self.ip += 1
        if self.ip > NODE_MAX_INSTR - 1 or self.ip > len(self.instr) - 1:
            self.ip = 0
        return self.instr[self.ip]

    def read_from(self, src):
        assert src in PORT_REGISTERS
        value = None
        self.blocked = True
        self.state = NODE_STATE_READ
        if self.regs[src] is not None:
            value = self.regs[src]
            self.regs[src] = None
        return value

    def write(self, dest, value):
        assert dest in PORT_REGISTERS
        self.blocked = True
        self.state = NODE_STATE_WRITE
        self.regs[dest] = value

    def before_cycle(self):
        instr = self.fetch()
        if self.deadlock and self.state == NODE_STATE_READ:
            #print self.id, "deadlock", self.state
            direction = instr.src
            neighbor = self.neighbors[direction]
            value = neighbor.read_port(direction)
            if value is not None:
                self.regs[direction] = value
                self.blocked = False
                self.deadlock = False
                self.state = NODE_STATE_IDLE
            else:
                return

    def after_cycle(self):
        if self.blocked:
            self.deadlock = True

    def read_port(self, direction):
        value = None
        opp_dir = self.opposite_dir(direction)
        if self.regs[opp_dir] is not None and self.blocked is True:
            value = self.regs[opp_dir]
            self.regs[opp_dir] = None
            if value is not None:
                self.blocked = False
                self.deadlock = False
                self.state = NODE_STATE_IDLE
                self.fetch_next()
        return value

    def cycle(self):
        self.cycle_count += 1

        if len(self.instr) < 1:
            return

        instr = self.fetch()

        if self.blocked:
            return
        #print '[', self.id, ']', self.ip, self.state, ':', instr, self.regs

        is_jumping = False

        # MOV
        if instr.type == INSTR_MOV:
            self.blocked = True
            src = instr.src
            dest = instr.dest
            value = None

            if instr.src_type == SRC_TYPE_INT:
                value = int(src)
            elif src in PORT_REGISTERS:
                value = self.read_from(src)
                if value is None:
                    return
            else:
                value = self.regs[dest] = self.regs[src]

            if dest in PORTS_LIST:
                self.write(dest, value)
                return
            else:
                self.regs[dest] = value

            self.blocked = False
        # ADD
        elif instr.type == INSTR_ADD:
            src = instr.src
            if src in PORT_REGISTERS:
                self.blocked = True
                value = self.read_from(src)
                if value is None:
                    return
                self.regs[REG_ACC] = clamp(self.regs[REG_ACC] + value)
                self.blocked = False
            elif instr.src_type == SRC_TYPE_REG:
                self.regs[REG_ACC] = clamp(self.regs[REG_ACC] + self.regs[src])
            elif instr.src_type == SRC_TYPE_INT:
                self.regs[REG_ACC] = clamp(self.regs[REG_ACC] + int(src))
            else:
                raise Exception()
        # SUB
        elif instr.type == INSTR_SUB:
            src = instr.src
            if src in PORT_REGISTERS:
                self.blocked = True
                value = self.read_from(src)
                if value is None:
                    return
                self.regs[REG_ACC] = clamp(self.regs[REG_ACC] - value)
                self.blocked = False
            elif instr.src_type == SRC_TYPE_REG:
                self.regs[REG_ACC] = clamp(self.regs[REG_ACC] - self.regs[src])
            elif instr.src_type == SRC_TYPE_INT:
                self.regs[REG_ACC] = clamp(self.regs[REG_ACC] - int(src))
            else:
                raise Exception()
        # NEG
        elif instr.type == INSTR_NEG:
            self.regs[REG_ACC] = -self.regs[REG_ACC]
        # SAV
        elif instr.type == INSTR_SAV:
            self.regs[REG_BAK] = self.regs[REG_ACC]
        # SWP
        elif instr.type == INSTR_SWP:
            tmp = self.regs[REG_BAK]
            self.regs[REG_BAK] = self.regs[REG_ACC]
            self.regs[REG_ACC] = tmp
        # JMP
        elif instr.type == INSTR_JMP:
            addr = self.symtable.get(instr.src)
            self.ip = int(addr)
            is_jumping = True
        # JEZ
        elif instr.type == INSTR_JEZ:
            if self.regs[REG_ACC] == 0:
                addr = self.symtable.get(instr.src)
                self.ip = int(addr)
                is_jumping = True
        # JNZ
        elif instr.type == INSTR_JNZ:
            if self.regs[REG_ACC] != 0:
                addr = self.symtable.get(instr.src)
                self.ip = int(addr)
                is_jumping = True
        # JGZ
        elif instr.type == INSTR_JGZ:
            if self.regs[REG_ACC] > 0:
                addr = self.symtable.get(instr.src)
                self.ip = int(addr)
                is_jumping = True
        # JLZ
        elif instr.type == INSTR_JLZ:
            if self.regs[REG_ACC] < 0:
                addr = self.symtable.get(instr.src)
                self.ip = int(addr)
                is_jumping = True
        # JRO
        elif instr.type == INSTR_JRO:
            addr = self.regs[REG_ACC]
            self.ip = addr
            is_jumping = True
        # HALT
        elif instr.type == INSTR_HCF:
            # HCF Halt and Catch Fire
            self.halted = True
        elif instr.type == INSTR_NOP:
            pass
        else:
            print 'Unknown opcode',

        self.state = NODE_STATE_RUN

        #print self.regs

        if not is_jumping:
            self.fetch_next()


class InputNode(BasicExecutionNode):
    def __init__(self, _id=None):
        super(InputNode, self).__init__(_id)
        self.regs = { REG_ACC: 0,
                      REG_LEFT: None, REG_RIGHT: None, REG_UP: None, REG_DOWN: None }
        self.values = []
        self.end_reached = False

    def __repr__(self):
        return "InputNode %i %s\n" % (self.id, self.instr)

    def fetch_next(self):
        self.ip += 1
        if self.ip > len(self.values) - 1:
            self.end_reached = True
        else:
            return self.values[self.ip]

    def cycle(self):
        self.cycle_count += 1

        if len(self.values) < 1:
            return
        if self.blocked or self.end_reached:
            return

        #print '[', self.id, ']', self.ip, self.state, ':', instr

        # MOV
        self.blocked = True

        value = self.values[self.ip]
        dest = self.neighbors.keys()[0]

        if dest in PORTS_LIST:
            self.write(dest, value)
            return
        else:
            raise Exception()
        #     self.regs[dest] = value
        #
        # self.blocked = False
        #
        # self.fetch_next()


class OutputNode(BasicExecutionNode):
    def __init__(self, _id=None):
        super(OutputNode, self).__init__(_id)
        self.regs = { REG_ACC: 0,
                      REG_LEFT: None, REG_RIGHT: None, REG_UP: None, REG_DOWN: None }
        self.values = []
        self.len_objective = 0

    def __repr__(self):
        return "OutputNode %i %s\n" % (self.id, self.instr)

    def fetch_next(self):
        pass

    def before_cycle(self):
        if self.deadlock and self.state == NODE_STATE_READ:
            #print self.id, "deadlock", self.state
            direction = self.neighbors.keys()[0]
            neighbor = self.neighbors[direction]
            value = neighbor.read_port(direction)
            if value is not None:
                #self.values.append(value)
                self.regs[direction] = value
                self.blocked = False
                self.deadlock = False
                self.state = NODE_STATE_IDLE
            else:
                return

    def cycle(self):
        self.cycle_count += 1

        if self.blocked:
            return

        #print '[', self.id, ']', self.ip, self.state, ':', instr

        # MOV
        self.blocked = True

        # value = self.values[self.ip]
        src = self.neighbors.keys()[0]

        if src in PORT_REGISTERS:
            value = self.read_from(src)
            if value is None:
                return
            self.values.append(value)
        else:
            raise Exception()
            #value = self.regs[dest] = self.regs[src]

        self.blocked = False

        # self.fetch_next()