import re
from collections import OrderedDict
from Enums import *

TCOMMAND = 'TCOMMAND'
TREGISTER = 'TREGISTER'
TINTEGER = 'TINTEGER'
TIDENTIFIER = 'TIDENTIFIER'
TSYMBOL = 'TSYMBOL'
TNONE = 'NONE'
#TWHITESPACE

lang_tokens = [TCOMMAND, TREGISTER, TINTEGER, TIDENTIFIER, TSYMBOL, TNONE]


KW_NOP = 'NOP'
KW_MOV = 'MOV'
KW_SWP = 'SWP'
KW_SAV = 'SAV'
KW_ADD = 'ADD'
KW_SUB = 'SUB'
KW_NEG = 'NEG'
KW_JMP = 'JMP'
KW_JEZ = 'JEZ'
KW_JNZ = 'JNZ'
KW_JGZ = 'JGZ'
KW_JLZ = 'JLZ'
KW_JRO = 'JRO'
KW_HALT = 'HALT'

lang_commands = [KW_NOP, KW_MOV, KW_SWP, KW_SAV, KW_ADD, KW_SUB, KW_NEG,
                 KW_JMP, KW_JEZ, KW_JNZ, KW_JGZ, KW_JLZ, KW_JRO, KW_HALT]

KW_ACC   = 'ACC'
KW_BAK   = 'BAK'
KW_NIL   = 'NIL'
KW_LEFT  = 'LEFT'
KW_RIGHT = 'RIGHT'
KW_UP    = 'UP'
KW_DOWN  = 'DOWN'
KW_ANY   = 'ANY'
KW_LAST  = 'LAST'

lang_registers = [KW_ACC, KW_BAK, KW_NIL, KW_LEFT, KW_RIGHT, KW_UP, KW_DOWN, KW_ANY, KW_LAST]

class Token(object):
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __repr__(self):
        value = self.value
        if self.type == TSYMBOL or self.type == TIDENTIFIER:
            value = '"%s"' % self.value
        return "Token(%s, %s)" % (self.type, value)

class Tokenizer(object):
    def __init__(self):
        self.defs = OrderedDict()
        self.option = {}
        self.option['lineno'] = True
        self.option['uppercase'] = False
        self.option['oneline_comment_start'] = '//'
        self.lines_number = []
        self.line_pos = 0

    def init(self):
        pass

    def on_error(self, message):
        pass

    def define_token(self, name, pattern):
        self.defs[name] = pattern

    def define_token_list(self, name, array):
        self.defs[name] = '^' + '(?=\s|\Z)|^'.join(array) + '(?=\s|\Z)'

    def define_simple_token_list(self, name, array):
        self.defs[name] = '|'.join(array)

    def make_token(self, word):
        for token_type, token_value in self.defs.iteritems():
            if re.match(token_value, word) is not None:
                return Token(token_type, word)
        return None

    def tokenize(self, sourcecode):
        lines = self._remove_comments(sourcecode).splitlines()
        patterns = ""
        for k, v in self.defs.iteritems():
            patterns += v + '|'
        if len(patterns) > 0:
            patterns = patterns[:-1]
        word = re.compile(patterns)

        lines_count = 0
        tokens = []
        for line in lines:
            lines_count += 1
            line_tokens = word.findall(line)
            if len(line_tokens) > 0:
                tokens.extend(self._line_to_tokens(line_tokens, lines_count))
                for i in range(len(line_tokens)):
                    self.lines_number.append(lines_count)
        return tokens

    def _line_to_tokens(self, raw_tokens, lines_count):
        tokens = []
        for el in raw_tokens:
            token = self.make_token(el)
            if token is not None:
                tokens.append(token)
            else:
                raise Exception("Unknown token at line %d" % lines_count)
        return tokens

    def _remove_comments(self, sourcecode):
        comment_id = self.option['oneline_comment_start']
        return re.sub(comment_id + r'.*?$', '', sourcecode, 0, re.MULTILINE)



class Lexer(Tokenizer):
    def __init__(self):
        super(Lexer, self).__init__()
        self._tokens = []
        self._index = -1 # tokens & lines index

    def lex(self, _input, _type='sourcecode'):
        if _type == "file":
            f = open(_input, 'r')
            self._tokens = self.tokenize(f.read())
            f.close()
        else:
            self._tokens = self.tokenize(_input)
        if len(self._tokens) > 0:
            print "tokens:", self._tokens


    def has_more_tokens(self):
        return self._index < len(self._tokens) - 1

    def advance(self):
        self._index += 1
        self.current_token = self._tokens[self._index]
        self.line_pos = self.lines_number[self._index]

    def peek_next_token(self):
        if self.has_more_tokens():
            return self._tokens[self._index + 1]
        return None


class TISLexer(Lexer):
    def __init__(self):
        super(TISLexer, self).__init__()
        self.option['uppercase'] = False
        self.option['oneline_comment_start'] = '#'
        self.define_token_list(TCOMMAND, lang_commands)
        self.define_token_list(TREGISTER, lang_registers)
        self.define_simple_token_list(TSYMBOL, [':', ','])
        self.define_token(TINTEGER, r'-?[0-9]+')
        self.define_token(TIDENTIFIER, r'[a-zA-Z0-9_]+[a-zA-Z0-9_]*')