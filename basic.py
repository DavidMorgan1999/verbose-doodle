# Imports
from string_arrows import *
    
import string
    
# constants
DIGITS = '0123456789'
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS
    

# errros 

class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details
    
    def as_string(self):
        result  = f'{self.error_name}: {self.details}\n'
        result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}'
        result += '\n\n' + string_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

class UnwantedCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Unwanted Character', details)

class ExpectedCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Expcted Character', details)

class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'Invalid Syntax', details)

class RunTimeError(Error):
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, 'Runtime Error', details)
        self.context = context

    def as_string(self):
        result  = self.gentrace()
        result += f'{self.error_name}: {self.details}'
        result += '\n\n' + string_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

    def gentrace(self):
        result = ''
        pos = self.pos_start
        ctx = self.context

        while ctx:
            result = f'  File {pos.fn}, line {str(pos.ln + 1)}, in {ctx.display_name}\n' + result
            pos = ctx.parent_entry_pos
            ctx = ctx.parent

        return 'Traceback :\n' + result


#positibn
# keeps position of index, line, column etc...
class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt
    
    # Advance the `pos` pointer and set the `current_char` variable
    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1

        if current_char == '\n':
            self.ln += 1
            self.col = 0

        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)

#tokens
INETEGER, FLOAT, IDENTIFIER, KEYWORD, EOF = 'INETEGER', 'FLOAT', 'IDENTIFIER', 'KEYWORD', 'EOF'
PLUS, MINUS, MULTIPLY, DIVIDE, POWER, EQUALS, LPARENT, RPARENT = 'PLUS', 'MINUS', 'MULTIPLY', 'DIVIDE', 'POWER', 'EQUALS', 'LPARENT', 'RPARENT'
DOUBLEEQUALS, NOTEQUALS, LESSTHAN, GREATERTHAN, LESSTHANEQUALS, GREATERTHANEQUALS = 'DOUBLEEQUALS', 'NOTEQUALS', 'LESSTHAN', 'GREATERTHAN', 'LESSTHANEQUALS', 'GREATERTHANEQUALS' 
COMMA, ARROW, STRING, LBRACKET, RBRACKET = 'COMMA','ARROW','STRING','LBRACKET','RBRACKET'
KEYWORDS = [
    'VARIABLE',
    'ADDITIONALLY',
    'ALTERNATIVELY',
    'NOT',
    'IF',
    'ORIF',
    'ELSE',
    'FOR',
    'TO',
    'STEP',
    'WHILE',
    'FUN',
    'DO'
]


class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()

        if pos_end:
            self.pos_end = pos_end.copy()

    def matches(self, type_, value):
        return self.type == type_ and self.value == value
    
    def __repr__(self):
        if self.value: return f'{self.type}:{self.value}'
        return f'{self.type}'

#lexer
class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.advance()
    
    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

    def make_tokens(self):
        tokens = []

        while self.current_char != None:
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_num())
            elif self.current_char in LETTERS:
                tokens.append(self.make_identifier())
            elif self.current_char == '"':
                tokens.append(self.make_string())
            elif self.current_char == '+':
                tokens.append(Token(PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '-':
                tokens.append(self.make_minus_or_arrow())
            elif self.current_char == '*':
                tokens.append(Token(MULTIPLY, pos_start=self.pos))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(DIVIDE, pos_start=self.pos))
                self.advance()
            elif self.current_char == '^':
                tokens.append(Token(POWER, pos_start=self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(LPARENT, pos_start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(RPARENT, pos_start=self.pos))
                self.advance()
            elif self.current_char == '[':
                tokens.append(Token(LBRACKET, pos_start=self.pos))
                self.advance()
            elif self.current_char == ']':
                tokens.append(Token(RBRACKET, pos_start=self.pos))
                self.advance()
            elif self.current_char == '!':
                token, error = self.make_not_equals()
                if error: return [], error
                tokens.append(token)
            elif self.current_char == '=':
                tokens.append(self.make_equals())
            elif self.current_char == '<':
                tokens.append(self.make_less_than())
            elif self.current_char == '>':
                tokens.append(self.make_greater_than())
            elif self.current_char == ',':
                tokens.append(Token(COMMA, pos_start=self.pos))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], UnwantedCharError(pos_start, self.pos, "'" + char + "'")

        tokens.append(Token(EOF, pos_start=self.pos))
        return tokens, None
    
    def make_string(self):
        string = ''
        pos_start = self.pos.copy()
        self.advance()
        
        while self.current_char != None and self.current_char != '"':
            string += self.current_char
            self.advance()
        
        self.advance()
        return Token(STRING, string, pos_start, self.pos)
            
    
    def make_num(self):
        num_str = ''
        dot_count = 0
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_count == 1: break
                dot_count += 1
            num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(INETEGER, int(num_str), pos_start, self.pos)
        else:
            return Token(FLOAT, float(num_str), pos_start, self.pos)

    def make_identifier(self):
        id_str = ''
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in LETTERS_DIGITS + '_':
            id_str += self.current_char
            self.advance()

        tok_type = KEYWORD if id_str in KEYWORDS else IDENTIFIER
        return Token(tok_type, id_str, pos_start, self.pos)

    def make_minus_or_arrow(self):
        tok_type = MINUS
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '>':
            self.advance()
            tok_type = ARROW

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            return Token(NOTEQUALS, pos_start=pos_start, pos_end=self.pos), None

        self.advance()
        return None, ExpectedCharError(pos_start, self.pos, "'=' (after '!')")
    
    def make_equals(self):
        tok_type = EQUALS
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = DOUBLEEQUALS

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_less_than(self):
        tok_type = LESSTHAN
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = LESSTHANEQUALS

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_greater_than(self):
        tok_type = GREATERTHAN
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = GREATERTHANEQUALS

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)


# Nodes

class NumNode:
    def __init__(self, tok):
        self.tok = tok

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self):
        return f'{self.tok}'

class StringNode:
    def __init__(self, tok):
        self.tok = tok

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self):
        return f'{self.tok}'
    
class ListNode:
    def __init__(self, element_nodes, pos_start, pos_end):
        self.element_nodes = element_nodes
        
        self.pos_start = pos_start
        self.pos_end = pos_end

class VariableAccessNode:
    def __init__(self, variable_name_tok):
        self.variable_name_tok = variable_name_tok

        self.pos_start = self.variable_name_tok.pos_start
        self.pos_end = self.variable_name_tok.pos_end

class VariableAssignNode:
    def __init__(self, variable_name_tok, value_node):
        self.variable_name_tok = variable_name_tok
        self.value_node = value_node

        self.pos_start = self.variable_name_tok.pos_start
        self.pos_end = self.value_node.pos_end

class BinaryOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node

        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self):
        return f'({self.left_node}, {self.op_tok}, {self.right_node})'

class UnaryOpNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node
        # gets first element of tuple whch would be expression
        self.pos_start = self.op_tok.pos_start
        self.pos_end = node.pos_end

    def __repr__(self):
        return f'({self.op_tok}, {self.node})'

class IfNode:
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case = else_case

        self.pos_start = self.cases[0][0].pos_start
        self.pos_end = (self.else_case or self.cases[len(self.cases) - 1][0]).pos_end

class ForNode:
    def __init__(self, variable_name_tok, start_value_node, end_value_node, step_value_node, body_node):
        self.variable_name_tok = variable_name_tok
        self.start_value_node = start_value_node
        self.end_value_node = end_value_node
        self.step_value_node = step_value_node
        self.body_node = body_node

        self.pos_start = self.variable_name_tok.pos_start
        self.pos_end = self.body_node.pos_end

class WhileNode:
    def __init__(self, condition_node, body_node):
        self.condition_node = condition_node
        self.body_node = body_node

        self.pos_start = self.condition_node.pos_start
        self.pos_end = self.body_node.pos_end

class FuncDefNode:
    def __init__(self, variable_name_tok, arg_name_toks, body_node):
        self.variable_name_tok = variable_name_tok
        self.arg_name_toks = arg_name_toks
        self.body_node = body_node

        if self.variable_name_tok:
            self.pos_start = self.variable_name_tok.pos_start
        elif len(self.arg_name_toks) > 0:
            self.pos_start = self.arg_name_toks[0].pos_start
        else:
            self.pos_start = self.body_node.pos_start

        self.pos_end = self.body_node.pos_end

class CallNode:
    def __init__(self, node_to_call, arg_nodes):
        self.node_to_call = node_to_call
        self.arg_nodes = arg_nodes

        self.pos_start = self.node_to_call.pos_start

        if len(self.arg_nodes) > 0:
            self.pos_end = self.arg_nodes[len(self.arg_nodes) - 1].pos_end
        else:
            self.pos_end = self.node_to_call.pos_end


#parse
class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.last_registered_advance_count = 0
        self.advance_count = 0

    def register_advancement(self):
        self.last_registered_advance_count = 1
        self.advance_count += 1

    def register(self, res):
        self.last_registered_advance_count = res.advance_count
        self.advance_count += res.advance_count
        if res.error: self.error = res.error
        return res.node

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        if not self.error or self.last_registered_advance_count == 0:
            self.error = error
        return self

#PASER

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.advance()

    def advance(self, ):
        self.tok_idx += 1
        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]
        return self.current_tok

    def parse(self):
        res = self.expr()
        if not res.error and self.current_tok.type != EOF:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '+', '-', '*', '/', '^', '==', '!=', '<', '>', <=', '>=', 'ADDITIONALLY' or 'ALTERNATIVELY'"
            ))
        return res

# if-expr, fragment, exponent, factor, term , math-expr, comp-expr, expr etc...(see grammar.txt)

    def expr(self):
        res = ParseResult()

        if self.current_tok.matches(KEYWORD, 'VARIABLE'):
            res.register_advancement()
            self.advance()

            if self.current_tok.type != IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected identifier"
                ))

            variable_name = self.current_tok
            res.register_advancement()
            self.advance()

            if self.current_tok.type != EQUALS:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected '='"
                ))

            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            return res.success(VariableAssignNode(variable_name, expr))

        node = res.register(self.binary_op(self.comp_expr, ((KEYWORD, 'ADDITIONALLY'), (KEYWORD, 'ALTERNATIVELY'))))

        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'VARIABLE', 'IF', 'FOR', 'WHILE', 'FUN', int, float, identifier, '+', '-', '(','[' or 'NOT'"
            ))

        return res.success(node)

    def comp_expr(self):
        res = ParseResult()

        if self.current_tok.matches(KEYWORD, 'NOT'):
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()

            node = res.register(self.comp_expr())
            if res.error: return res
            return res.success(UnaryOpNode(op_tok, node))
        
        node = res.register(self.binary_op(self.math_expr, (DOUBLEEQUALS, NOTEQUALS, LESSTHAN, GREATERTHAN, LESSTHANEQUALS, GREATERTHANEQUALS)))
        
        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected int, float, identifier, '+', '-', '(','[' or 'NOT'"
            ))

        return res.success(node)

    def math_expr(self):
        return self.binary_op(self.term, (PLUS, MINUS))

    def term(self):
        return self.binary_op(self.factor, (MULTIPLY, DIVIDE))

    def factor(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (PLUS, MINUS):
            res.register_advancement()
            self.advance()
            factor = res.register(self.factor())
            if res.error: return res
            return res.success(UnaryOpNode(tok, factor))

        return self.exponent()

    def exponent(self):
        return self.binary_op(self.call, (POWER, ), self.factor)

    def call(self):
        res = ParseResult()
        fragment = res.register(self.fragment())
        if res.error: return res

        if self.current_tok.type == LPARENT:
            res.register_advancement()
            self.advance()
            arg_nodes = []

            if self.current_tok.type == RPARENT:
                res.register_advancement()
                self.advance()
            else:
                arg_nodes.append(res.register(self.expr()))
                if res.error:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected ')', 'VARIABLE', 'IF', 'FOR', 'WHILE', 'FUN', int, float, identifier, '+', '-', '(','[' or 'NOT'"
                    ))

                while self.current_tok.type == COMMA:
                    res.register_advancement()
                    self.advance()

                    arg_nodes.append(res.register(self.expr()))
                    if res.error: return res

                if self.current_tok.type != RPARENT:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        f"Expected ',' or ')'"
                    ))

                res.register_advancement()
                self.advance()
            return res.success(CallNode(fragment, arg_nodes))
        return res.success(fragment)

    def fragment(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (INETEGER, FLOAT):
            res.register_advancement()
            self.advance()
            return res.success(NumNode(tok))

        if tok.type == STRING:
            res.register_advancement()
            self.advance()
            return res.success(StringNode(tok))
        
        elif tok.type == IDENTIFIER:
            res.register_advancement()
            self.advance()
            return res.success(VariableAccessNode(tok))

        elif tok.type == LPARENT:
            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            if self.current_tok.type == RPARENT:
                res.register_advancement()
                self.advance()
                return res.success(expr)
            else:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ')'"
                ))
        elif tok.type == LBRACKET:
            list_expr = res.register(self.list_expr())
            if res.error: return res
            return res.success(list_expr)

        elif tok.matches(KEYWORD, 'IF'):
            if_expr = res.register(self.if_expr())
            if res.error: return res
            return res.success(if_expr)

        elif tok.matches(KEYWORD, 'FOR'):
            for_expr = res.register(self.for_expr())
            if res.error: return res
            return res.success(for_expr)

        elif tok.matches(KEYWORD, 'WHILE'):
            while_expr = res.register(self.while_expr())
            if res.error: return res
            return res.success(while_expr)

        elif tok.matches(KEYWORD, 'FUN'):
            func_def = res.register(self.func_def())
            if res.error: return res
            return res.success(func_def)

        return res.failure(InvalidSyntaxError(
            tok.pos_start, tok.pos_end,
            "Expected int, float, identifier, '+', '-', '(', '[', 'IF', 'FOR', 'WHILE', 'FUN'"
        ))

    def list_expr(self):
        res = ParseResult()
        element_nodes = []
        pos_start = self.current_tok.pos_start.copy()
        
        if self.current_tok.type != LBRACKET:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '['"
            ))
        res.register_advancement()
        self.advance()
        
        if self.current_tok.type == RBRACKET:
            res.register_advancement()
            self.advance()
        else:
            #this code is the same as in call 
            element_nodes.append(res.register(self.expr()))
            if res.error:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ']', 'VARIABLE', 'IF', 'FOR', 'WHILE', 'FUN', int, float, identifier, '+', '-', '(','[' or 'NOT'"
                    ))

            while self.current_tok.type == COMMA:
                res.register_advancement()
                self.advance()

                element_nodes.append(res.register(self.expr()))
                if res.error: return res

            if self.current_tok.type != RBRACKET:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected ',' or ']'"
                    ))

            res.register_advancement()
            self.advance()
        return res.success(ListNode(
            element_nodes, pos_start, self.current_tok.pos_end.copy()
            ))
        
    def if_expr(self):
        res = ParseResult()
        cases = []
        else_case = None

        if not self.current_tok.matches(KEYWORD, 'IF'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'IF'"
            ))

        res.register_advancement()
        self.advance()
        # conidtion for the if statement i.e if (condition) do (thing)
        condition = res.register(self.expr())
        if res.error: return res

        if not self.current_tok.matches(KEYWORD, 'DO'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'DO'"
            ))

        res.register_advancement()
        self.advance()
        # thing for the if statement i.e if (condition) do (thing)
        expr = res.register(self.expr())
        if res.error: return res
        cases.append((condition, expr))
        # does same for any Orifs
        while self.current_tok.matches(KEYWORD, 'ORIF'):
            res.register_advancement()
            self.advance()

            condition = res.register(self.expr())
            if res.error: return res

            if not self.current_tok.matches(KEYWORD, 'DO'):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected 'DO'"
                ))

            res.register_advancement()
            self.advance()

            expr = res.register(self.expr())
            if res.error: return res
            cases.append((condition, expr))

        if self.current_tok.matches(KEYWORD, 'ELSE'):
            res.register_advancement()
            self.advance()

            else_case = res.register(self.expr())
            if res.error: return res

        return res.success(IfNode(cases, else_case))

    def for_expr(self):
        res = ParseResult()

        if not self.current_tok.matches(KEYWORD, 'FOR'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'FOR'"
            ))

        res.register_advancement()
        self.advance()
        # Looks for variable names
        if self.current_tok.type != IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected identifier"
            ))

        variable_name = self.current_tok
        res.register_advancement()
        self.advance()

        if self.current_tok.type != EQUALS:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '='"
            ))
        
        res.register_advancement()
        self.advance()

        start_value = res.register(self.expr())
        if res.error: return res

        if not self.current_tok.matches(KEYWORD, 'TO'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'TO'"
            ))
        
        res.register_advancement()
        self.advance()

        end_value = res.register(self.expr())
        if res.error: return res
        # optional step and expression
        if self.current_tok.matches(KEYWORD, 'STEP'):
            res.register_advancement()
            self.advance()

            step_value = res.register(self.expr())
            if res.error: return res
        else:
            step_value = None

        if not self.current_tok.matches(KEYWORD, 'DO'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'DO'"
            ))

        res.register_advancement()
        self.advance()

        body = res.register(self.expr())
        if res.error: return res

        return res.success(ForNode(variable_name, start_value, end_value, step_value, body))

    def while_expr(self):
        res = ParseResult()

        if not self.current_tok.matches(KEYWORD, 'WHILE'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'WHILE'"
            ))

        res.register_advancement()
        self.advance()

        condition = res.register(self.expr())
        if res.error: return res

        if not self.current_tok.matches(KEYWORD, 'DO'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'DO'"
            ))

        res.register_advancement()
        self.advance()

        body = res.register(self.expr())
        if res.error: return res

        return res.success(WhileNode(condition, body))

    def func_def(self):
        res = ParseResult()

        if not self.current_tok.matches(KEYWORD, 'FUN'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'FUN'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type == IDENTIFIER:
            variable_name_tok = self.current_tok
            res.register_advancement()
            self.advance()
            if self.current_tok.type != LPARENT:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected '('"
                ))
        else:
            variable_name_tok = None
            if self.current_tok.type != LPARENT:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected identifier or '('"
                ))
        
        res.register_advancement()
        self.advance()
        arg_name_toks = []

        if self.current_tok.type == IDENTIFIER:
            arg_name_toks.append(self.current_tok)
            res.register_advancement()
            self.advance()
            
            while self.current_tok.type == COMMA:
                res.register_advancement()
                self.advance()

                if self.current_tok.type != IDENTIFIER:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        f"Expected identifier"
                    ))

                arg_name_toks.append(self.current_tok)
                res.register_advancement()
                self.advance()
            
            if self.current_tok.type != RPARENT:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected ',' or ')'"
                ))
        else:
            if self.current_tok.type != RPARENT:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected identifier or ')'"
                ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type != ARROW:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '->'"
            ))

        res.register_advancement()
        self.advance()
        node_to_return = res.register(self.expr())
        if res.error: return res

        return res.success(FuncDefNode(
            variable_name_tok,
            arg_name_toks,
            node_to_return
        ))


    def binary_op(self, func_a, ops, func_b=None):
        if func_b == None:
            func_b = func_a
        
        res = ParseResult()
        left = res.register(func_a())
        if res.error: return res

        while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops:
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()
            right = res.register(func_b())
            if res.error: return res
            left = BinaryOpNode(left, op_tok, right)

        return res.success(left)


# RunTime
class RunTimeResult:
    def __init__(self):
        self.value = None
        self.error = None

    def register(self, res):
        self.error = res.error
        return res.value

    def success(self, value):
        self.value = value
        return self

    def failure(self, error):
        self.error = error
        return self

#values
class Value:
    def __init__(self):
        self.set_pos()
        self.set_context()

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def plussed(self, other):
        return None, self.illegal_operation(other)

    def minused(self, other):
        return None, self.illegal_operation(other)

    def multiplied(self, other):
        return None, self.illegal_operation(other)

    def divided(self, other):
        return None, self.illegal_operation(other)

    def topowerof(self, other):
        return None, self.illegal_operation(other)

    def get_equals(self, other):
        return None, self.illegal_operation(other)

    def get_notequals(self, other):
        return None, self.illegal_operation(other)

    def get_lessthan(self, other):
        return None, self.illegal_operation(other)

    def get_greaterthan(self, other):
        return None, self.illegal_operation(other)

    def get_lessthanequals(self, other):
        return None, self.illegal_operation(other)

    def get_greaterthanequals(self, other):
        return None, self.illegal_operation(other)

    def additionally(self, other):
        return None, self.illegal_operation(other)

    def alternatively(self, other):
        return None, self.illegal_operation(other)

    def notted(self, other):
        return None, self.illegal_operation(other)

    def execute(self, args):
        return RunTimeResult().failure(self.illegal_operation())

    def copy(self):
        raise Exception('No copy method defined')

    def is_true(self):
        return False

    def illegal_operation(self, other=None):
        if not other: other = self
        return RunTimeError(
            self.pos_start, other.pos_end,
            'Illegal operation',
            self.context
        )

class Num(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def plussed(self, other):
        if isinstance(other, Num):
            return Num(self.value + other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def minused(self, other):
        if isinstance(other, Num):
            return Num(self.value - other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def multiplied(self, other):
        if isinstance(other, Num):
            return Num(self.value * other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def divided(self, other):
        if isinstance(other, Num):
            if other.value == 0:
                return None, RunTimeError(
                    other.pos_start, other.pos_end,
                    'Division by zero',
                    self.context
                )

            return Num(self.value / other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def topowerof(self, other):
        if isinstance(other, Num):
            return Num(self.value ** other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_equals(self, other):
        if isinstance(other, Num):
            return Num(int(self.value == other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_notequals(self, other):
        if isinstance(other, Num):
            return Num(int(self.value != other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_lessthan(self, other):
        if isinstance(other, Num):
            return Num(int(self.value < other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_greaterthan(self, other):
        if isinstance(other, Num):
            return Num(int(self.value > other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_lessthanequals(self, other):
        if isinstance(other, Num):
            return Num(int(self.value <= other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_greaterthanequals(self, other):
        if isinstance(other, Num):
            return Num(int(self.value >= other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def additionally(self, other):
        if isinstance(other, Num):
            return Num(int(self.value and other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def alternatively(self, other):
        if isinstance(other, Num):
            return Num(int(self.value or other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def notted(self):
        return Num(1 if self.value == 0 else 0).set_context(self.context), None

    def copy(self):
        copy = Num(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def is_true(self):
        return self.value != 0
    
    def __repr__(self):
        return str(self.value)
    
class String(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value
        
    def plussed(self, other):
        if isinstance(other, String):
            return String(self.value + other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)
    
    def multiplied(self, other):
        if isinstance(other, Num):
            return String(self.value * other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)
        
    def is_true(self):
        return len(self.value) >= 1
    
    def copy(self):
        copy = String(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return str(self.value)
    
class List(Value):
        def __init__(self, elements):
            super().__init__()
            self.elements = elements
        
        def minused(self, other):
            if isinstance(other, Num):
                new_list = self.copy()
                try:
                    new_list.elements.pop(other.value)
                    return new_list,None    
                except:
                    return None, RunTimeError(other.pos_start, other.pos_end, 'Index uout of bounds', self.context)
            else:
                return None, Value.illegal_operation(self, other)
        
        def plussed(self, other):
            new_list = self.copy()
            new_list.elements.append(other)
            return new_list, None
        
        def multiplied(self, other):
            if isinstance(other, List):
                new_list = self.copy()
                new_list.elements.extend(other.elements)
                return new_list,None    
            else:
                return None, Value.illegal_operation(self, other)
            
        def divided(self, other):
            if isinstance(other, Num):
                try:
                    return self.elements[other.value],None    
                except:
                    return None, RunTimeError(other.pos_start, other.pos_end, 'Index uout of bounds', self.context)
            else:
                return None, Value.illegal_operation(self, other)
            
        def copy(self):
            copy = List(self.elements[:])
            copy.set_pos(self.pos_start, self.pos_end)
            copy.set_context(self.context)
            return copy
        
        def __repr__(self):
            return f'[{", ".join([str(x) for x in self.elements])}]'
        
        
class Function(Value):
    def __init__(self, name, body_node, arg_names):
        super().__init__()
        self.name = name or "<anonymous>"
        self.body_node = body_node
        self.arg_names = arg_names

    def execute(self, args):
        res = RunTimeResult()
        interpreter = Interpreter()
        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)

        if len(args) > len(self.arg_names):
            return res.failure(RunTimeError(
                self.pos_start, self.pos_end,
                f"{len(args) - len(self.arg_names)} too many args passed into '{self.name}'",
                self.context
            ))
        
        if len(args) < len(self.arg_names):
            return res.failure(RunTimeError(
                self.pos_start, self.pos_end,
                f"{len(self.arg_names) - len(args)} too few args passed into '{self.name}'",
                self.context
            ))

        for i in range(len(args)):
            arg_name = self.arg_names[i]
            arg_value = args[i]
            arg_value.set_context(new_context)
            new_context.symbol_table.set(arg_name, arg_value)

        value = res.register(interpreter.visit(self.body_node, new_context))
        if res.error: return res
        return res.success(value)

    def copy(self):
        copy = Function(self.name, self.body_node, self.arg_names)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<function {self.name}>"

#context

class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None


# symbosl
class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def get(self, name):
        value = self.symbols.get(name, None)
        if value == None and self.parent:
            return self.parent.get(name)
        return value

    def set(self, name, value):
        self.symbols[name] = value

    def remove(self, name):
        del self.symbols[name]


# INTERPRETER


class Interpreter:
    def visit(self, node, context):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)

    def no_visit_method(self, node, context):
        raise Exception(f'No visit_{type(node).__name__} method defined')


    def visit_NumNode(self, node, context):
        return RunTimeResult().success(
            Num(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
        )
    def visit_StringNode(self, node, context):
        return RunTimeResult().success(
            String(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
            )
        
    def visit_ListNode(self, node, context):
        res = RunTimeResult()
        elements = []
        
        for element_node in node.element_nodes:
            elements.append(res.register(self.visit(element_node, context)))
            if res.error: return res

        return res.success(
        List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )
    
    def visit_VariableAccessNode(self, node, context):
        res = RunTimeResult()
        variable_name = node.variable_name_tok.value
        value = context.symbol_table.get(variable_name)

        if not value:
            return res.failure(RunTimeError(
                node.pos_start, node.pos_end,
                f"'{variable_name}' is not defined",
                context
            ))

        value = value.copy().set_pos(node.pos_start, node.pos_end)
        return res.success(value)

    def visit_VariableAssignNode(self, node, context):
        res = RunTimeResult()
        variable_name = node.variable_name_tok.value
        value = res.register(self.visit(node.value_node, context))
        if res.error: return res

        context.symbol_table.set(variable_name, value)
        return res.success(value)

    def visit_BinaryOpNode(self, node, context):
        res = RunTimeResult()
        left = res.register(self.visit(node.left_node, context))
        if res.error: return res
        right = res.register(self.visit(node.right_node, context))
        if res.error: return res

        if node.op_tok.type == PLUS:
            result, error = left.plussed(right)
        elif node.op_tok.type == MINUS:
            result, error = left.minused(right)
        elif node.op_tok.type == MULTIPLY:
            result, error = left.multiplied(right)
        elif node.op_tok.type == DIVIDE:
            result, error = left.divided(right)
        elif node.op_tok.type == POWER:
            result, error = left.topowerof(right)
        elif node.op_tok.type == DOUBLEEQUALS:
            result, error = left.get_equals(right)
        elif node.op_tok.type == NOTEQUALS:
            result, error = left.get_notequals(right)
        elif node.op_tok.type == LESSTHAN:
            result, error = left.get_lessthan(right)
        elif node.op_tok.type == GREATERTHAN:
            result, error = left.get_greaterthan(right)
        elif node.op_tok.type == LESSTHANEQUALS:
            result, error = left.get_lessthanequals(right)
        elif node.op_tok.type == GREATERTHANEQUALS:
            result, error = left.get_greaterthanequals(right)
        elif node.op_tok.matches(KEYWORD, 'ADDITIONALLY'):
            result, error = left.additionally(right)
        elif node.op_tok.matches(KEYWORD, 'ALTERNATIVELY'):
            result, error = left.alternatively(right)

        if error:
            return res.failure(error)
        else:
            return res.success(result.set_pos(node.pos_start, node.pos_end))

    def visit_UnaryOpNode(self, node, context):
        res = RunTimeResult()
        num = res.register(self.visit(node.node, context))
        if res.error: return res

        error = None

        if node.op_tok.type == MINUS:
            num, error = num.multiplied(Num(-1))
        elif node.op_tok.matches(KEYWORD, 'NOT'):
            num, error = num.notted()

        if error:
            return res.failure(error)
        else:
            return res.success(num.set_pos(node.pos_start, node.pos_end))

    def visit_IfNode(self, node, context):
        res = RunTimeResult()

        for condition, expr in node.cases:
            condition_value = res.register(self.visit(condition, context))
            if res.error: return res

            if condition_value.is_true():
                expr_value = res.register(self.visit(expr, context))
                if res.error: return res
                return res.success(expr_value)

        if node.else_case:
            else_value = res.register(self.visit(node.else_case, context))
            if res.error: return res
            return res.success(else_value)

        return res.success(None)

    def visit_ForNode(self, node, context):
        res = RunTimeResult()
        elements = []
        start_value = res.register(self.visit(node.start_value_node, context))
        if res.error: return res

        end_value = res.register(self.visit(node.end_value_node, context))
        if res.error: return res

        if node.step_value_node:
            step_value = res.register(self.visit(node.step_value_node, context))
            if res.error: return res
        else:
            step_value = Num(1)

        i = start_value.value

        if step_value.value >= 0:
            condition = lambda: i < end_value.value
        else:
            condition = lambda: i > end_value.value
        
        while condition():
            context.symbol_table.set(node.variable_name_tok.value, Num(i))
            i += step_value.value

            elements.append(res.register(self.visit(node.body_node, context)))
            if res.error: return res

        return res.success(
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_WhileNode(self, node, context):
        res = RunTimeResult()
        elements = []
        
        while True:
            condition = res.register(self.visit(node.condition_node, context))
            if res.error: return res

            if not condition.is_true(): break

            elements.append(res.register(self.visit(node.body_node, context)))
            if res.error: return res

        return res.success(
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_FuncDefNode(self, node, context):
        res = RunTimeResult()

        func_name = node.variable_name_tok.value if node.variable_name_tok else None
        body_node = node.body_node
        arg_names = [arg_name.value for arg_name in node.arg_name_toks]
        func_value = Function(func_name, body_node, arg_names).set_context(context).set_pos(node.pos_start, node.pos_end)
        
        if node.variable_name_tok:
            context.symbol_table.set(func_name, func_value)

        return res.success(func_value)

    def visit_CallNode(self, node, context):
        res = RunTimeResult()
        args = []

        value_to_call = res.register(self.visit(node.node_to_call, context))
        if res.error: return res
        value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node, context)))
            if res.error: return res

        return_value = res.register(value_to_call.execute(args))
        if res.error: return res
        return res.success(return_value)

#Run
globalsymbol_table = SymbolTable()
globalsymbol_table.set("NULL", Num(0))
globalsymbol_table.set("FALSE", Num(0))
globalsymbol_table.set("TRUE", Num(1))

def run(fn, text):
    # Generate tokens
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error: return None, error
    
    # Generate AST
    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error: return None, ast.error

    # Run program
    interpreter = Interpreter()
    context = Context('<program>')
    context.symbol_table = globalsymbol_table
    result = interpreter.visit(ast.node, context)

    return result.value, result.error
