class SymbolTable:
    def __init__(self):
        self.symbols = {}          
        self.parent = None         
        self.level = 0             

    def add(self, name, info):
        self.symbols[name.lower()] = info

    def lookup(self, name):
        name = name.lower()
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent:
            return self.parent.lookup(name)
        return None

    def lookup_current_scope(self, name):
        return self.symbols.get(name.lower())

    def create_child_scope(self):
        child = SymbolTable()
        child.parent = self
        child.level = self.level + 1
        return child


class SemanticAnalyzer:
    def __init__(self):
        self.global_scope = SymbolTable()
        self.current_scope = self.global_scope
        self.errors = []
        self.warnings = []
        self.in_loop = False
        self.in_lhs_of_assignment = False

    def analyze(self, ast):
        self.errors = [] # Limpar erros anteriores
        self.warnings = []
        if ast:
            try:
                self.visit(ast)
            except Exception as e:
                import traceback
                traceback.print_exc() # Debug útil
                self.add_error(f"Erro interno durante análise semântica: {str(e)}")
        return len(self.errors) == 0, self.errors, self.warnings

    def add_error(self, msg, node=None):
        prefix = ""
        if node and hasattr(node, 'lineno') and node.lineno:
            prefix = f"[Linha {node.lineno}] "
        self.errors.append(f"{prefix}{msg}")

    def add_warning(self, msg, node=None):
        prefix = ""
        if node and hasattr(node, 'lineno') and node.lineno:
            prefix = f"[Linha {node.lineno}] "
        self.warnings.append(f"{prefix}{msg}")

    def enter_scope(self):
        self.current_scope = self.current_scope.create_child_scope()

    def exit_scope(self):
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent

    def visit(self, node):
        if not node: return 'unknown'
        method_name = f'visit_{node.type}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        if hasattr(node, 'children'):
            for child in node.children:
                if child:
                    self.visit(child)
        return 'unknown'

    # --- ESTRUTURA ---

    def visit_Program(self, node):
        if node.children: self.visit(node.children[0])

    def visit_Block(self, node):
        # --- CORREÇÃO CRÍTICA DE ORDEM ---
        # O parser envia [Functions, Declarations, Body] ou variações.
        # TEMOS de visitar Declarations (Vars Globais) PRIMEIRO para que as Funções as vejam.
        
        funcs = None
        decls = None
        body = None

        # Identifica os nós filhos baseados no tipo, não na posição
        for child in node.children:
            if child.type == 'Declarations':
                decls = child
            elif child.type == 'FunctionDeclarations':
                funcs = child
            elif child.type == 'CompoundStatement':
                body = child

        # Ordem Correta: 1. Vars, 2. Funções, 3. Corpo
        if decls: self.visit(decls)
        if funcs: self.visit(funcs)
        if body: self.visit(body)

    def visit_Declarations(self, node):
        for child in node.children:
            if child and child.type != 'Empty': self.visit(child)

    def visit_Declaration(self, node):
        id_list = node.children[0]
        type_node = node.children[1]
        type_info = self.get_type_info(type_node)

        # Suporte a id_list plana ou aninhada
        ids = id_list.children if id_list.type == 'IDList' else [id_list]

        for child in ids:
            var_name = child.leaf
            if self.current_scope.lookup_current_scope(var_name):
                self.add_error(f"Variável '{var_name}' já declarada neste escopo.", child)
            else:
                self.current_scope.add(var_name, {
                    'kind': 'variable',
                    'type': type_info,
                    'initialized': False
                })

    def get_type_info(self, type_node):
        if type_node.type == 'BasicType': return type_node.leaf 
        elif type_node.type == 'Type': return type_node.leaf
        elif type_node.type == 'ArrayType':
            range_tuple = type_node.leaf
            # Correção: ArrayType filho 0 pode ser BasicType ou Type
            elem_type = self.get_type_info(type_node.children[0])
            return {'kind': 'array', 'range': range_tuple, 'elem_type': elem_type}
        return 'unknown'

    # --- SUBPROGRAMAS ---

    def visit_FunctionDeclarations(self, node):
        for child in node.children: self.visit(child)

    def visit_ProcedureDeclaration(self, node):
        proc_name = node.leaf
        if self.current_scope.lookup_current_scope(proc_name):
            self.add_error(f"Procedimento '{proc_name}' já declarado.", node)
        else:
            # Guardamos os parametros para validar a chamada depois
            params_info = self._extract_params(node.children[0])
            proc_info = {'kind': 'procedure', 'params': params_info}
            self.current_scope.add(proc_name, proc_info)

        self.enter_scope()
        self._register_params_in_scope(node.children[0])
        
        if len(node.children) > 2:
            self.visit(node.children[2]) # Body
        self.exit_scope()

    def visit_FunctionDeclaration(self, node):
        func_name = node.leaf 
        return_type = self.get_type_info(node.children[1])
        
        if self.current_scope.lookup_current_scope(func_name):
            self.add_error(f"Função '{func_name}' já declarada.", node)
        else:
            params_info = self._extract_params(node.children[0])
            func_info = {'kind': 'function', 'params': params_info, 'return_type': return_type}
            self.current_scope.add(func_name, func_info)

        self.enter_scope()
        # Adiciona variável de retorno (mesmo nome da função)
        self.current_scope.add(func_name, {'kind': 'variable', 'type': return_type, 'initialized': False})
        self._register_params_in_scope(node.children[0])

        if len(node.children) > 2:
            self.visit(node.children[2]) 
        self.exit_scope()

    # Helpers para Parâmetros
    def _extract_params(self, params_node):
        params = []
        if params_node.type == 'FormalParameters':
            for param in params_node.children:
                p_ids = param.children[0]
                ids = p_ids.children if p_ids.type == 'IDList' else [p_ids]
                p_type = self.get_type_info(param.children[1])
                for _ in ids:
                    params.append(p_type)
        return params

    def _register_params_in_scope(self, params_node):
        if params_node.type == 'FormalParameters':
            for param in params_node.children:
                p_ids = param.children[0]
                ids = p_ids.children if p_ids.type == 'IDList' else [p_ids]
                p_type = self.get_type_info(param.children[1])
                for p_id in ids:
                    self.current_scope.add(p_id.leaf, {'kind': 'variable', 'type': p_type, 'initialized': True})

    # --- COMANDOS ---

    def visit_CompoundStatement(self, node):
        # CORREÇÃO: Percorrer TODAS as instruções do bloco, não apenas a primeira
        for child in node.children:
            if child:
                self.visit(child)

    def visit_StatementList(self, node):
        for child in node.children:
            if child: self.visit(child)

    def visit_AssignmentStatement(self, node): 
        self.in_lhs_of_assignment = True
        var_node = node.children[0]
        var_type = self.visit(var_node)
        self.in_lhs_of_assignment = False

        expr_type = self.visit(node.children[1])

        if var_type and expr_type and var_type != 'error' and expr_type != 'error':
            if not self.check_type_compatibility(var_type, expr_type):
                self.add_error(f"Incompatibilidade: Tentativa de atribuir '{expr_type}' a '{var_type}'.", node)
        
        # Marca como inicializada
        if var_node.type == 'VariableAccess': 
            info = self.current_scope.lookup(var_node.leaf)
            if info: info['initialized'] = True

    def visit_IfStatement(self, node):
        cond_type = self.visit(node.children[0])
        if cond_type != 'boolean' and cond_type != 'error':
            self.add_error(f"A condição do 'if' deve ser booleana, recebeu '{cond_type}'.", node.children[0])
        
        self.visit(node.children[1]) 
        if len(node.children) > 2: self.visit(node.children[2]) 

    def visit_WhileStatement(self, node):
        cond_type = self.visit(node.children[0])
        if cond_type != 'boolean' and cond_type != 'error':
            self.add_error("A condição do 'while' deve ser booleana.", node.children[0])
        self.visit(node.children[1])

    def visit_ForStatement(self, node):
        var_name = node.children[0].leaf
        var_info = self.current_scope.lookup(var_name)
        if not var_info:
            self.add_error(f"Variável de controle '{var_name}' não declarada.", node)
        else:
            var_info['initialized'] = True

        start_t = self.visit(node.children[1])
        end_t = self.visit(node.children[2])

        if (start_t != 'integer' and start_t != 'error') or (end_t != 'integer' and end_t != 'error'):
            self.add_error("Limites do 'for' devem ser inteiros.", node)

        self.visit(node.children[3]) 

    # --- EXPRESSÕES ---

    def visit_VariableAccess(self, node):
        name = node.leaf
        info = self.current_scope.lookup(name)
        if not info:
            self.add_error(f"Identificador '{name}' não declarado.", node)
            return 'error' 
        
        if not self.in_lhs_of_assignment and not info.get('initialized', False):
            # Opcional: Warning
            # self.add_warning(f"Variável '{name}' pode não ter sido inicializada.", node)
            pass

        return info['type']

    def visit_ArrayAccess(self, node):
        name = node.leaf
        info = self.current_scope.lookup(name)
        
        if not info:
            self.add_error(f"Array '{name}' não declarado.", node)
            return 'error'

        type_info = info['type']
        is_array = isinstance(type_info, dict) and type_info.get('kind') == 'array'
        is_string = type_info == 'string'

        if not is_array and not is_string:
            self.add_error(f"Variável '{name}' não é indexável (não é array nem string).", node)
            return 'error'

        index_type = self.visit(node.children[0])
        if index_type != 'integer' and index_type != 'error':
            self.add_error(f"Índice de array deve ser inteiro.", node.children[0])

        if is_string: return 'string' # Pascal retorna char, mas aqui tratamos como string de tam 1
        return type_info['elem_type']

    def visit_BinaryOp(self, node):
        left_t = self.visit(node.children[0])
        right_t = self.visit(node.children[1])
        op = node.leaf

        if left_t == 'error' or right_t == 'error':
            return 'error'

        # Operações Matemáticas
        if op in ['+', '-', '*', 'DIV', 'MOD', '/']:
            if left_t == 'integer' and right_t == 'integer':
                return 'integer'
            if left_t == 'real' or right_t == 'real': # Suporte básico a real
                return 'real'
            
            self.add_error(f"Operação '{op}' requer tipos numéricos. Recebeu '{left_t}' e '{right_t}'.", node)
            return 'error'

        # Comparações
        if op in ['=', '<>', '<', '>', '<=', '>=']:
            if self.check_type_compatibility(left_t, right_t):
                return 'boolean'
            self.add_error(f"Comparação inválida entre '{left_t}' e '{right_t}'.", node)
            return 'error'

        # Lógica
        if op in ['AND', 'OR']:
            if left_t == 'boolean' and right_t == 'boolean':
                return 'boolean'
            self.add_error(f"Operador lógico '{op}' requer booleanos.", node)
            return 'error'

        return 'error'

    def visit_UnaryOp(self, node):
        expr_t = self.visit(node.children[0])
        if expr_t == 'error': return 'error'

        op = node.leaf
        if op == 'NOT':
            if expr_t != 'boolean': 
                self.add_error("NOT requer booleano.", node)
                return 'error'
            return 'boolean'
        elif op == 'MINUS':
            if expr_t != 'integer' and expr_t != 'real': 
                self.add_error("Menos unário requer número.", node)
                return 'error'
            return expr_t
        return expr_t

    # --- LITERAIS ---
    def visit_IntegerConstant(self, node): return 'integer'
    def visit_RealConstant(self, node): return 'real'     # CORREÇÃO: Faltava este
    def visit_StringConstant(self, node): return 'string'
    def visit_BooleanConstant(self, node): return 'boolean'
    def visit_NumericConst(self, node): return 'integer'

    # --- CHAMADAS ---

    def visit_FunctionCall(self, node):
        func_name = node.leaf
        info = self.current_scope.lookup(func_name)
        if not info:
            if func_name == 'length': return 'integer' # Built-in simples
            self.add_error(f"Função '{func_name}' não declarada.", node)
            return 'error'
        
        if info['kind'] != 'function':
            self.add_error(f"'{func_name}' não é uma função.", node)
            return 'error'

        # Validação de Argumentos (Simples)
        self._check_args(node, info['params'], func_name)
        return info['return_type']

    # CORREÇÃO: Faltava visit_ProcedureCall
    def visit_ProcedureCall(self, node):
        proc_name = node.leaf
        
        # Ignorar built-ins de I/O por agora (são tratados como statements especiais no parser, 
        # mas se forem chamados como ProcedureCall, convém ignorar ou validar manualmente)
        if proc_name in ['write', 'writeln', 'read', 'readln']:
            return

        info = self.current_scope.lookup(proc_name)
        if not info:
            self.add_error(f"Procedimento '{proc_name}' não declarado.", node)
            return
        
        if info['kind'] != 'procedure':
            self.add_error(f"'{proc_name}' não é um procedimento.", node)
            return

        self._check_args(node, info['params'], proc_name)

    def _check_args(self, node, expected_params, name):
        # node.children[0] é ArgList se houver argumentos
        args_node = node.children[0] if node.children else None
        given_args = []
        
        if args_node and args_node.type == 'ArgList':
            for arg in args_node.children:
                t = self.visit(arg)
                given_args.append(t)
        
        if len(given_args) != len(expected_params):
            self.add_error(f"'{name}' espera {len(expected_params)} argumentos, recebeu {len(given_args)}.", node)
            return

        for i, (expected, given) in enumerate(zip(expected_params, given_args)):
            if not self.check_type_compatibility(expected, given):
                self.add_error(f"Argumento {i+1} de '{name}': esperava '{expected}', recebeu '{given}'.", node)

    # --- I/O ---
    def visit_ReadStatement(self, node):
        for var in node.children:
            self.in_lhs_of_assignment = True
            t = self.visit(var)
            self.in_lhs_of_assignment = False
            
            # Validação básica de read
            if t not in ['integer', 'real', 'string', 'error']:
                 self.add_error(f"Não é possível ler para variável do tipo '{t}'.", var)

            if var.type == 'VariableAccess':
                info = self.current_scope.lookup(var.leaf)
                if info: info['initialized'] = True

    def visit_WriteStatement(self, node):
        for expr in node.children: self.visit(expr)

    # --- UTIL ---
    def check_type_compatibility(self, expected, actual):
        if expected == 'error' or actual == 'error': return True 
        if expected == actual: return True
        if expected == 'string' and actual == 'string': return True
        if expected == 'real' and actual == 'integer': return True # Coerção implícita
        return False