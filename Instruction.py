from Enums import *

class Instruction(object):

    def __init__(self, _type, _src=None, _dest=None):
        self.type = _type
        self.value = None
        self.src = _src
        self.dest = _dest
        self.src_type = SRC_TYPE_NONE
        self.line_num = 0 # TODO

        if self.type == INSTR_LABEL:
            self.value = _src
            self.src = None
        elif self.type in REGISTERS_SET:
            raise Exception()

        if self.src in REGISTERS_SET:
           self.src_type = SRC_TYPE_REG
        elif type(self.src) is int:
           self.src_type = SRC_TYPE_INT

    def __repr__(self):
        if self.dest is not None and self.src is not None:
            return "%s <%s> <%s>" % (self.type, self.src, self.dest)
        if self.src is not None:
            return "%s <%s>" % (self.type, self.src)
        else:
            if self.value is not None:
                return '%s "%s"' % (self.type, self.value)
            else:
                return "%s" % self.type
