import re
from lexer import Lexer

class Parser:
    def __init__(self):
        self.lexer = Lexer()
        self.in_function = False
        self.main_found = False
        self.symbol_table = {}
        self.block_stack = []
        self.temp_count = 0
        self.label_count = 0
        self.intermediate_code = []
        self.current_function = None
        self.loop_stack = []
        self.pending_else = None  # Track pending else after an if

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def parse_line(self, line, line_number):
        tokens = self.lexer.tokenize(line)
        if not tokens:
            return

        if tokens[0][0] == 'PREPROCESSOR':
            return

        types = [t[0] for t in tokens]
        values = [t[1] for t in tokens]

        print(f"Line {line_number} Tokens:")
        for token in tokens:
            print(f"  {token[0]} -> {token[1]}")

        # Function start: e.g. int main() {
        if (len(tokens) >= 5 and
            tokens[0][0] == 'KEYWORD' and
            tokens[1][0] == 'IDENTIFIER' and
            tokens[2][1] == '(' and
            ')' in values and
            '{' in values):
            self.in_function = True
            self.block_stack.append('function')
            self.current_function = tokens[1][1]
            if self.current_function == 'main':
                self.main_found = True
            self.symbol_table[self.current_function] = 'function'
            self.intermediate_code.append(f"func {self.current_function}:")
            return

        # Block start (if, else, while, for) with '{'
        if tokens[0][1] in ('if', 'while', 'for', 'else') and '{' in values:
            self.block_stack.append('block')

            keyword = tokens[0][1]
            if keyword == 'while':
                # while condition block: generate loop labels and jumps
                cond_start_label = self.new_label()
                cond_true_label = self.new_label()
                cond_end_label = self.new_label()
                self.loop_stack.append((cond_start_label, cond_true_label, cond_end_label))
                self.intermediate_code.append(f"{cond_start_label}:")
                cond_expr = self.extract_condition_expr(tokens)
                cond_temp = self.generate_expression_code(cond_expr)
                self.intermediate_code.append(f"if {cond_temp} goto {cond_true_label}")
                self.intermediate_code.append(f"goto {cond_end_label}")
                self.intermediate_code.append(f"{cond_true_label}:")
            elif keyword == 'for':
                # For loop has init; cond; inc parts inside ()
                cond_start_label = self.new_label()
                cond_true_label = self.new_label()
                cond_end_label = self.new_label()
                self.loop_stack.append((cond_start_label, cond_true_label, cond_end_label))
                # Parse for init; cond; inc separately
                init_expr, cond_expr, inc_expr = self.extract_for_expr(tokens)
                # Init code
                if init_expr:
                    self.process_for_init(init_expr)
                self.intermediate_code.append(f"{cond_start_label}:")
                # Condition code
                cond_temp = self.generate_expression_code(cond_expr)
                self.intermediate_code.append(f"if {cond_temp} goto {cond_true_label}")
                self.intermediate_code.append(f"goto {cond_end_label}")
                self.intermediate_code.append(f"{cond_true_label}:")
                # Save inc_expr for later after block end
                self.loop_stack[-1] += (inc_expr,)
            elif keyword == 'if':
                # if condition block
                cond_expr = self.extract_condition_expr(tokens)
                cond_temp = self.generate_expression_code(cond_expr)
                else_label = self.new_label()
                end_label = self.new_label()
                self.block_stack.append('block')
                self.intermediate_code.append(f"if not {cond_temp} goto {else_label}")
                self.pending_else = (else_label, end_label)  # Save for the else
                self.loop_stack.append((else_label, end_label))  # Save for matching else


            elif keyword == 'else':
                if self.pending_else:
                    else_label, end_label = self.pending_else
                    self.intermediate_code.append(f"goto {end_label}")
                    self.intermediate_code.append(f"{else_label}:")
                    self.block_stack.append('block')
                    self.loop_stack.append(('else', end_label))  # Mark the end label for this else
                    self.pending_else = None
                else:
                    raise SyntaxError(f"Syntax error at line {line_number}: unexpected 'else' without matching 'if'")
            return

        # Block end: '}'
        if line.strip() == '}':
            if not self.block_stack:
                raise SyntaxError(f"Syntax error at line {line_number}: unmatched closing brace")

            last_block = self.block_stack.pop()

            # Handle loop ends
            if last_block == 'function':
                self.in_function = False
                self.current_function = None
                return

            if last_block == 'block':
                if self.pending_else:
                    return
                if not self.loop_stack:
                    return
                top = self.loop_stack[-1]
                if len(top) == 3:  # while or for loop
                    start_label, true_label, end_label = self.loop_stack.pop()
                    # For 'for' loops, inc_expr is saved as 4th element
                    inc_expr = None
                    if len(top) == 4:
                        inc_expr = top[3]
                    # For loops: generate increment code then jump back to cond start
                    if inc_expr:
                        inc_code = self.generate_expression_code(inc_expr)
                        self.intermediate_code.extend(inc_code)
                    self.intermediate_code.append(f"goto {start_label}")
                    self.intermediate_code.append(f"{end_label}:")
                elif len(top) == 2:  # if block
                    else_label, end_label = self.loop_stack.pop()
                    self.intermediate_code.append(f"{end_label}:")
                elif isinstance(top, tuple) and top[0] == 'else':
                    end_label = top[1]
                    self.loop_stack.pop()
                    self.intermediate_code.append(f"{end_label}:")

                return

            # if last_block == 'if':
            #     # We close if block without else
            #     if self.pending_else:
            #         else_label, end_label = self.pending_else
            #         self.intermediate_code.append(f"{else_label}:")
            #         self.intermediate_code.append(f"{end_label}:")
            #         self.pending_else = None  
            #     return

        if not self.in_function or not self.block_stack:
            raise SyntaxError(f"Syntax error at line {line_number}: Not inside function block")

        # Variable declaration with initialization
        if tokens[0][0] == 'KEYWORD' and 'IDENTIFIER' in types and '=' in values and tokens[-1][1] == ';':
            var_name = tokens[1][1]
            self.symbol_table[var_name] = 'variable'
            rhs_expr = [v for t, v in tokens[3:-1]]
            expr_temp = self.generate_expression_code(rhs_expr)
            self.intermediate_code.extend(expr_temp[1:])
            self.intermediate_code.append(f"{var_name} = {expr_temp[0]}")
            return

        # Variable declaration without initialization
        if tokens[0][0] == 'KEYWORD' and 'IDENTIFIER' in types and tokens[-1][1] == ';':
            var_name = tokens[1][1]
            self.symbol_table[var_name] = 'variable'
            return

        # Assignment statement
        if tokens[0][0] == 'IDENTIFIER' and '=' in values and tokens[-1][1] == ';':
            var_name = tokens[0][1]
            rhs_expr = [v for t, v in tokens[2:-1]]
            expr_temp = self.generate_expression_code(rhs_expr)
            self.intermediate_code.extend(expr_temp[1:])
            self.intermediate_code.append(f"{var_name} = {expr_temp[0]}")
            return

        # Return statement
        if tokens[0][1] == 'return' and tokens[-1][1] == ';':
            if len(tokens) > 2:
                ret_expr = [v for t, v in tokens[1:-1]]
                expr_temp = self.generate_expression_code(ret_expr)
                self.intermediate_code.extend(expr_temp[1:])
                self.intermediate_code.append(f"return {expr_temp[0]}")
            else:
                self.intermediate_code.append("return")
            return

        # Function call statement
        if (tokens[0][0] == 'IDENTIFIER' and tokens[1][1] == '(' and ')' in values and tokens[-1][1] == ';'):
            func_name = tokens[0][1]
            args = [v for t, v in tokens[2:-2] if v != ',']
            temp = self.new_temp()
            arg_str = ', '.join(args)
            self.intermediate_code.append(f"{temp} = call {func_name}({arg_str})")
            return

        # Print statement
        if (tokens[0][1] == 'print' and tokens[1][1] == '(' and ')' in values and tokens[-1][1] == ';'):
            args = [v for t, v in tokens[2:-2] if v != ',']
            self.intermediate_code.append(f"print({', '.join(args)})")
            return

        raise SyntaxError(f"Syntax error at line {line_number}: {line.strip()}")

    def extract_condition_expr(self, tokens):
        # Extract tokens inside first pair of ()
        start = None
        end = None
        for i, (t, v) in enumerate(tokens):
            if v == '(':
                start = i + 1
                break
        if start is None:
            return []
        for j in range(start, len(tokens)):
            if tokens[j][1] == ')':
                end = j
                break
        if end is None:
            return []
        expr = [tokens[i][1] for i in range(start, end)]
        return expr

    def extract_for_expr(self, tokens):
        # Extract init; cond; inc from for(...) tokens
        start = None
        end = None
        for i, (t, v) in enumerate(tokens):
            if v == '(':
                start = i + 1
                break
        for j in range(len(tokens)-1, -1, -1):
            if tokens[j][1] == ')':
                end = j
                break
        if start is None or end is None:
            return [], [], []

        inner_tokens = tokens[start:end]
        semicolon_indices = [i for i, (t,v) in enumerate(inner_tokens) if v == ';']

        if len(semicolon_indices) != 2:
            return [], [], []

        init = [v for t,v in inner_tokens[:semicolon_indices[0]]]
        cond = [v for t,v in inner_tokens[semicolon_indices[0]+1:semicolon_indices[1]]]
        inc = [v for t,v in inner_tokens[semicolon_indices[1]+1:]]

        return init, cond, inc

    def process_for_init(self, init_expr):
        if not init_expr:
            return
        # For simplicity, only support assignment or declaration with init
        # e.g. int i = 0 or i = 0
        if init_expr[0] == 'int' and len(init_expr) > 2 and init_expr[2] == '=':
            var_name = init_expr[1]
            self.symbol_table[var_name] = 'variable'
            rhs_expr = init_expr[3:]
            expr_temp = self.generate_expression_code(rhs_expr)
            self.intermediate_code.extend(expr_temp[1:])
            self.intermediate_code.append(f"{var_name} = {expr_temp[0]}")
        elif '=' in init_expr:
            eq_idx = init_expr.index('=')
            var_name = init_expr[0]
            rhs_expr = init_expr[eq_idx+1:]
            expr_temp = self.generate_expression_code(rhs_expr)
            self.intermediate_code.extend(expr_temp[1:])
            self.intermediate_code.append(f"{var_name} = {expr_temp[0]}")

    def generate_expression_code(self, expr):
        # Very basic left-to-right parsing without operator precedence
        # returns list of instructions, last temp holding expression result is first element
        if not expr:
            return []

        code = []
        stack = []

        def is_operator(c):
            return c in ('+', '-', '*', '/', '<', '>', '<=', '>=', '==', '!=', '%')

        i = 0
        while i < len(expr):
            token = expr[i]
            if token.isdigit() or re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', token):
                stack.append(token)
                i += 1
            elif is_operator(token):
                # binary op, pop left, take right from next token
                left = stack.pop()
                op = token
                right = expr[i+1]
                temp = self.new_temp()
                code.append(f"{temp} = {left} {op} {right}")
                stack.append(temp)
                i += 2
            else:
                # If token is '(' or ')' or unknown, just skip for now
                i += 1

        if len(stack) == 1:
            return [stack[0]] + code
        else:
            # fallback join expression as is
            temp = self.new_temp()
            code.append(f"{temp} = {' '.join(expr)}")
            return [temp] + code

    def validate_main(self):
        if not self.main_found:
            raise SyntaxError("Program must start with a 'main' function.")

    def display_symbol_table(self):
        print("\nSymbol Table:")
        for symbol, kind in self.symbol_table.items():
            print(f"  {symbol} -> {kind}")

    def write_intermediate_code(self):
        with open("intermediate_code.txt", "w") as f:
            for line in self.intermediate_code:
                f.write(line + "\n")
        print("\nIntermediate code written to 'intermediate_code.txt'")
