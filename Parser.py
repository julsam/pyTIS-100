from Lexer import *
from Enums import *
from Instruction import Instruction
from SymbolTable import SymbolTable

class ParserError(Exception):
    def __init__(self, token_type=TNONE, token_value=None, line_pos=-1):
        if token_value is not None:
            error = "Expected %s '%s'" % (lang_tokens[token_type], token_value)
        else:
            error = "Expected %s" % token_type
        if line_pos >= 0:
            error += " at line %d" % line_pos
        self.args = [error]

class Parser(object):

    def __init__(self, symbol_table, instr):
        self.lexer = TISLexer()
        self.instr = instr
        self.symbol_table = symbol_table
        self.unresolved_symbols = [] # (id, addr)

    def parse(self, _input):
        self.lexer.lex(_input)
        while self.lexer.has_more_tokens():
            self.compile_tokens()
        self._resolve_symbols()
        if len(self.instr) > 0:
            print "parser instr :", self.instr

    def _resolve_symbols(self):
        for id, addr in self.unresolved_symbols:
            jump_addr = self.symbol_table.get(id)
            if jump_addr is None:
                Exception("Unresolved identifier %s" % id)
            else:
                self.instr[addr] = jump_addr

    def _expect(self, token_type, token_value=None):
        self._advance()
        if self.lexer.current_token.type != token_type:
            raise ParserError(token_type, token_value, self.lexer.line_pos)
        if token_value is not None:
            if self.lexer.current_token.value != token_value:
                raise ParserError(token_type, token_value, self.lexer.line_pos)
        return self.lexer.current_token.value

    def _expect_any(self, token_type, token_values_list=None):
        self._advance()
        if self.lexer.current_token.type != token_type:
            raise ParserError(token_type, token_values_list, self.lexer.line_pos)
        if token_values_list is not None:
            if self.lexer.current_token.value not in token_values_list:
                raise ParserError(token_type, token_values_list, self.lexer.line_pos)
        return self.lexer.current_token.value

    def _advance(self):
        if self.lexer.has_more_tokens():
            self.lexer.advance()
            return self.lexer.current_token.value

    def _is_token(self, token_type, token_value=None):
        token = self.lexer.peek_next_token()
        if token is None:
            return False
        if token_value is None:
            return token.type == token_type
        else:
            return token.type == token_type and token.value == token_value

    def _is_token_any(self, token_type, token_values_list):
        token = self.lexer.peek_next_token()
        if token is None:
            return False
        return token.type == token_type and token.value in token_values_list

    def compile_tokens(self):
        if self._is_token(TCOMMAND):
            self.compile_command()
        elif self._is_token(TIDENTIFIER):
            self._compile_label_addr()
        else:
            print self.lexer.peek_next_token()
            # todo fix this ugly shitty broken design for the line number
            raise ParserError(TCOMMAND, None, self.lexer.lines_number[self.lexer._index+1])

    def _compile_label_addr(self):
        label = self._expect(TIDENTIFIER)
        self._expect(TSYMBOL, ':')
        self.instr.append(Instruction(INSTR_LABEL, label))

    def compile_command(self):
        if self._is_token(TCOMMAND, KW_NOP):
            self._compile_nop()
        elif self._is_token(TCOMMAND, KW_MOV):
            self._compile_mov()
        elif self._is_token(TCOMMAND, KW_SWP):
            self._compile_swp()
        elif self._is_token(TCOMMAND, KW_SAV):
            self._compile_sav()
        elif self._is_token(TCOMMAND, KW_ADD):
            self._compile_add()
        elif self._is_token(TCOMMAND, KW_SUB):
            self._compile_sub()
        elif self._is_token(TCOMMAND, KW_NEG):
            self._compile_neg()
        elif self._is_token(TCOMMAND, KW_JMP):
            self._compile_jmp()
        elif self._is_token(TCOMMAND, KW_JEZ):
            self._compile_jez()
        elif self._is_token(TCOMMAND, KW_JNZ):
            self._compile_jnz()
        elif self._is_token(TCOMMAND, KW_JGZ):
            self._compile_jgz()
        elif self._is_token(TCOMMAND, KW_JLZ):
            self._compile_jlz()
        elif self._is_token(TCOMMAND, KW_JRO):
            self._compile_jro()
        elif self._is_token(TCOMMAND, KW_HCF):
            self._compile_halt()
        else:
            print self.lexer.peek_next_token()
            # todo fix this ugly shitty broken design for the line number
            raise ParserError(TCOMMAND, None, self.lexer.lines_number[self.lexer._index+1])

    def _compile_halt(self):
        self._expect(TCOMMAND, KW_HCF)
        self.instr.append(Instruction(KW_HCF))

    def _compile_nop(self):
        self._expect(TCOMMAND, KW_NOP)
        self.instr.append(Instruction(INSTR_NOP))

    def _compile_mov(self):
        self._expect(TCOMMAND, KW_MOV)
        src = None
        if self._is_token(TINTEGER):
            src = int(self._expect(TINTEGER))
        else:
            src = self._expect(TREGISTER)
        if self._is_token(TSYMBOL):
            self._expect(TSYMBOL, ',')
        dest = self._expect(TREGISTER)
        self.instr.append(Instruction(INSTR_MOV, src, dest))

    def _compile_swp(self):
        self._expect(TCOMMAND, KW_SWP)
        self.instr.append(Instruction(INSTR_SWP))

    def _compile_sav(self):
        self._expect(TCOMMAND, KW_SAV)
        self.instr.append(Instruction(INSTR_SAV))

    def _compile_add(self):
        self._expect(TCOMMAND, KW_ADD)
        src = None
        if self._is_token(TINTEGER):
            src = int(self._expect(TINTEGER))
        else:
            src = self._expect(TREGISTER)
        self.instr.append(Instruction(INSTR_ADD, src))

    def _compile_sub(self):
        self._expect(TCOMMAND, KW_SUB)
        src = None
        if self._is_token(TINTEGER):
            src = int(self._expect(TINTEGER))
        else:
            src = self._expect(TREGISTER)
        self.instr.append(Instruction(INSTR_SUB, src))

    def _compile_neg(self):
        self._expect(TCOMMAND, KW_NEG)
        self.instr.append(Instruction(INSTR_NEG))

    def _compile_jmp(self):
        self._expect(TCOMMAND, KW_JMP)
        label = self._expect(TIDENTIFIER)
        self.instr.append(Instruction(INSTR_JMP, label))

    def _compile_jez(self):
        self._expect(TCOMMAND, KW_JEZ)
        label = self._expect(TIDENTIFIER)
        self.instr.append(Instruction(INSTR_JEZ, label))

    def _compile_jnz(self):
        self._expect(TCOMMAND, KW_JNZ)
        label = self._expect(TIDENTIFIER)
        self.instr.append(Instruction(INSTR_JNZ, label))

    def _compile_jgz(self):
        self._expect(TCOMMAND, KW_JGZ)
        label = self._expect(TIDENTIFIER)
        self.instr.append(Instruction(INSTR_JGZ, label))

    def _compile_jlz(self):
        self._expect(TCOMMAND, KW_JLZ)
        label = self._expect(TIDENTIFIER)
        self.instr.append(Instruction(INSTR_JLZ, label))

    def _compile_jro(self):
        self._expect(TCOMMAND, KW_JRO)
        label = self._expect(TIDENTIFIER)
        self.instr.append(Instruction(INSTR_JRO, label))
