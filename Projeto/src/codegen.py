class CodeGenerator:
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self.code = []
        self.label_counter = 0
        self.variable_offsets = {}
        self.current_offset = 0
        self.procedure_starts = {}

    def generate(self, ast):
        self.visit(ast)
        return self.code

    def emit(self, instruction):
        self.code.append(instruction)

    def create_label(self):
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label

    def visit(self, node):
        if not node: return
        method_name = f'generate_{node.type}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        for child in node.children:
            self.visit(child)

    def _is_local(self):
        return '$return' in self.variable_offsets

    # Helper para endereços de memória
    def _emit_var_addr(self, offset):
        if offset < 0 or self._is_local():
            self.emit("PUSHFP")
        else:
            self.emit("PUSHGP")
        self.emit(f"PUSHI {offset}")
        self.emit("PADD")

    # -------------------------------------------------------------------------
    # ESTRUTURA DO PROGRAMA
    # -------------------------------------------------------------------------
    def generate_Program(self, node):
        self.emit("PUSHI 0") 
        self.emit("PUSHI 0") 
        self.emit("START")
        self.visit(node.children[0]) 
        self.emit("STOP")

    def generate_Block(self, node):
        self.visit(node.children[1]) # Aloca Globais
        lbl_main = self.create_label()
        self.emit(f"JUMP {lbl_main}")
        self.visit(node.children[0]) # Funções
        self.emit(f"{lbl_main}:")
        self.visit(node.children[2]) # Main

    def generate_Declarations(self, node):
        total_space = 0
        if node.children:
            decls = node.children if isinstance(node.children, list) else []
            for decl in decls:
                 if decl.type == 'Declaration':
                     total_space += self.process_declaration(decl)
        if total_space > 0:
            self.emit(f"PUSHN {total_space}")

    def process_declaration(self, node):
        id_list = node.children[0]
        type_node = node.children[1]
        size = 1 
        if type_node.type == 'ArrayType':
             r_min, r_max = type_node.leaf
             size = (r_max - r_min) + 1

        ids = id_list.children if id_list.type == 'IDList' else [id_list]
        for id_node in ids:
            var_name = id_node.leaf
            self.variable_offsets[var_name] = self.current_offset
            self.current_offset += size
        return size * len(ids)

    # -------------------------------------------------------------------------
    # SUBPROGRAMAS
    # -------------------------------------------------------------------------
    def generate_FunctionDeclarations(self, node):
        for child in node.children:
            self.visit(child)

    def generate_ProcedureDeclaration(self, node):
        self._generate_subprogram(node, is_function=False)

    def generate_FunctionDeclaration(self, node):
        self._generate_subprogram(node, is_function=True)

    def _generate_subprogram(self, node, is_function):
        name = node.leaf
        params = node.children[0]
        body = node.children[2]

        lbl = self.create_label()
        self.procedure_starts[name] = lbl
        self.emit(f"{lbl}:")

        old_offset = self.current_offset
        old_vars = self.variable_offsets.copy()
        self.variable_offsets = {}

        # --- 1. PARAMETROS (OFFSET -1) ---
        flat_params = []
        if params.children:
             for param in params.children:
                 id_list = param.children[0]
                 ids = id_list.children if id_list.type == 'IDList' else [id_list]
                 for id_node in ids:
                     flat_params.append(id_node.leaf)
        
        # MUDANÇA CRÍTICA: Começa em -1 (Baseado na tua imagem: FP=5, Arg=4)
        p_offset = -1
        for param_name in reversed(flat_params):
            self.variable_offsets[param_name] = p_offset
            p_offset -= 1

        # --- 2. LOCAIS ---
        self.current_offset = 0 
        if is_function:
            self.variable_offsets['$return'] = self.current_offset
            self.variable_offsets[name] = self.current_offset 
            self.current_offset += 1
            self.emit("PUSHI 0")

        self.visit(body)

        if is_function:
            self.emit(f"PUSHL {self.variable_offsets['$return']}")

        self.emit("RETURN")
        self.current_offset = old_offset
        self.variable_offsets = old_vars

    # -------------------------------------------------------------------------
    # COMANDOS
    # -------------------------------------------------------------------------
    def generate_CompoundStatement(self, node):
        for child in node.children:
            self.visit(child)

    def generate_IfStatement(self, node):
        lbl_else = self.create_label()
        lbl_end = self.create_label()
        self.visit(node.children[0])
        self.emit(f"JZ {lbl_else}")
        self.visit(node.children[1])
        self.emit(f"JUMP {lbl_end}")
        self.emit(f"{lbl_else}:")
        if len(node.children) > 2:
            self.visit(node.children[2])
        self.emit(f"{lbl_end}:")

    def generate_WhileStatement(self, node):
        lbl_start = self.create_label()
        lbl_end = self.create_label()
        self.emit(f"{lbl_start}:")
        self.visit(node.children[0])
        self.emit(f"JZ {lbl_end}")
        self.visit(node.children[1])
        self.emit(f"JUMP {lbl_start}")
        self.emit(f"{lbl_end}:")

    def generate_ForStatement(self, node):
        var_node = node.children[0]
        name = var_node.leaf
        offset = self.variable_offsets.get(name)
        direction = node.leaf
        
        is_stack = self._is_local() or offset < 0
        instr_store = f"STOREL {offset}" if is_stack else f"STOREG {offset}"
        instr_push = f"PUSHL {offset}" if is_stack else f"PUSHG {offset}"

        self.visit(node.children[1]) 
        self.emit(instr_store)

        lbl_loop = self.create_label()
        lbl_end = self.create_label()

        self.emit(f"{lbl_loop}:")
        self.emit(instr_push)
        self.visit(node.children[2]) 
        if direction == 'to': self.emit("INFEQ")
        else: self.emit("SUPEQ")
        self.emit(f"JZ {lbl_end}")

        self.visit(node.children[3]) 

        self.emit(instr_push)
        self.emit("PUSHI 1")
        if direction == 'to': self.emit("ADD")
        else: self.emit("SUB")
        self.emit(instr_store)
        
        self.emit(f"JUMP {lbl_loop}")
        self.emit(f"{lbl_end}:")

    # -------------------------------------------------------------------------
    # ACESSOS: ARRAYS E STRINGS (CHARAT)
    # -------------------------------------------------------------------------
    def generate_ArrayAccess(self, node):
        name = node.leaf
        info = self.symbol_table.lookup(name)
        
        # --- CORREÇÃO: STRINGS USAM CHARAT ---
        if info and info.get('type') == 'string':
            offset = self.variable_offsets.get(name)
            if self._is_local() or offset < 0:
                self.emit(f"PUSHL {offset}")
            else:
                self.emit(f"PUSHG {offset}")
            
            # Índice
            self.visit(node.children[0])
            
            # Ajuste Pascal 1-based
            self.emit("PUSHI 1")
            self.emit("SUB")
            
            self.emit("CHARAT")
            return

        # --- ARRAYS NORMAIS ---
        self._calc_array_addr(node)
        self.emit("LOAD 0")

    def _calc_array_addr(self, node):
        name = node.leaf
        offset = self.variable_offsets.get(name)
        self._emit_var_addr(offset)
        
        self.visit(node.children[0]) 
        
        info = self.symbol_table.lookup(name)
        if info and isinstance(info.get('type'), dict):
             r_min = info['type']['range'][0]
             if r_min != 0:
                 self.emit(f"PUSHI {r_min}")
                 self.emit("SUB")
        
        self.emit("PADD") 

    def generate_AssignmentStatement(self, node):
        var_node = node.children[0]
        expr = node.children[1]

        if var_node.type == 'ArrayAccess':
            self._calc_array_addr(var_node)
            self.visit(expr)
            self.emit("STORE 0") 
        else:
            self.visit(expr)
            name = var_node.leaf
            off = self.variable_offsets.get(name)
            if self._is_local() or off < 0:
                self.emit(f"STOREL {off}")
            else:
                self.emit(f"STOREG {off}")

    def generate_ReadStatement(self, node):
        for var in node.children:
            if var.type == 'ArrayAccess':
                self._calc_array_addr(var)
            
            self.emit("READ")
            
            var_name = var.leaf
            info = self.symbol_table.lookup(var_name)
            is_int = True
            if info:
                t = info['type']
                if isinstance(t, dict) and t.get('kind') == 'array':
                    if t.get('elem_type') != 'integer': is_int = False
                elif t == 'string': is_int = False
            
            if is_int: self.emit("ATOI")

            if var.type == 'ArrayAccess':
                self.emit("STORE 0")
            else:
                off = self.variable_offsets.get(var_name)
                if self._is_local() or off < 0:
                    self.emit(f"STOREL {off}")
                else:
                    self.emit(f"STOREG {off}")

    def generate_VariableAccess(self, node):
        name = node.leaf
        offset = self.variable_offsets.get(name)
        if offset is not None:
            if self._is_local() or offset < 0:
                self.emit(f"PUSHL {offset}")
            else:
                self.emit(f"PUSHG {offset}")

    # -------------------------------------------------------------------------
    # OUTPUT E HELPERS
    # -------------------------------------------------------------------------
    def generate_WriteStatement(self, node):
        for expr in node.children:
            self.visit(expr)
            if expr.type == 'StringConstant': self.emit("WRITES")
            else: self.emit("WRITEI")

    def generate_FunctionCall(self, node):
        name = node.leaf
        if name.lower() == 'length':
            if node.children:
                self.visit(node.children[0].children[0])
            self.emit("STRLEN")
            return

        if node.children:
            for arg in node.children[0].children:
                self.visit(arg)
        
        lbl = self.procedure_starts.get(name)
        if lbl:
            self.emit(f"PUSHA {lbl}")
            self.emit("CALL")

    def generate_BinaryOp(self, node):
        left = node.children[0]
        right = node.children[1]
        
        # Fix Comparação Char/String
        if (node.leaf == '=' or node.leaf == '<>') and \
           right.type == 'StringConstant' and len(right.leaf) == 1:
                self.visit(left)
                self.emit(f"PUSHI {ord(right.leaf)}")
                if node.leaf == '=': self.emit("EQUAL")
                else: 
                    self.emit("EQUAL")
                    self.emit("NOT")
                return

        self.visit(left)
        self.visit(right)
        ops = {'+':'ADD', '-':'SUB', '*':'MUL', 'DIV':'DIV', 'MOD':'MOD', 
               '=':'EQUAL', '<':'INF', '>':'SUP', '<=': 'INFEQ', '>=':'SUPEQ', 
               'AND':'AND', 'OR':'OR'}
        if node.leaf in ops: self.emit(ops[node.leaf])
        elif node.leaf == '<>': 
            self.emit("EQUAL")
            self.emit("NOT")

    def generate_UnaryOp(self, node):
        self.visit(node.children[0])
        if node.leaf == 'NOT': self.emit("NOT")
        elif node.leaf == 'MINUS': 
            self.emit("PUSHI -1")
            self.emit("MUL")

    def generate_IntegerConstant(self, node): self.emit(f"PUSHI {node.leaf}")
    def generate_NumericConst(self, node): self.emit(f"PUSHI {node.leaf}")
    def generate_BooleanConstant(self, node): 
        val = 1 if node.leaf.lower() == 'true' else 0
        self.emit(f"PUSHI {val}")
    def generate_StringConstant(self, node): self.emit(f'PUSHS "{node.leaf}"')