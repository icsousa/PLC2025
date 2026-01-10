from parser import Node

class Optimizer:
    def __init__(self):
        self.optimizations_count = 0

    def optimize(self, node):
        if not node or not isinstance(node, Node):
            return node

        # 1. Otimizar filhos (Bottom-Up)
        for i, child in enumerate(node.children):
            node.children[i] = self.optimize(child)

        # 2. Simplificar nó atual
        if node.type == 'BinaryOp':
            return self.fold_binary_op(node)
        elif node.type == 'UnaryOp':
            return self.fold_unary_op(node)
        elif node.type == 'IfStatement':
            return self.fold_if_statement(node)

        return node

    def fold_binary_op(self, node):
        left = node.children[0]
        right = node.children[1]
        op = node.leaf

        # CORREÇÃO: Usar 'IntegerConstant' em vez de 'NumericConst'
        # Adicionei também suporte para comparação simples de inteiros (=)
        if left.type == 'IntegerConstant' and right.type == 'IntegerConstant':
            v1 = left.leaf
            v2 = right.leaf
            res = None

            try:
                if op == '+': res = v1 + v2
                elif op == '-': res = v1 - v2
                elif op == '*': res = v1 * v2
                elif op == 'DIV': res = v1 // v2
                elif op == 'MOD': res = v1 % v2
                # Otimização extra: Comparações estáticas
                elif op == '=': 
                    # Transforma em BooleanConstant
                    self.optimizations_count += 1
                    return Node('BooleanConstant', [], 'true' if v1 == v2 else 'false', lineno=node.lineno)
            except ZeroDivisionError:
                return node

            if res is not None:
                self.optimizations_count += 1
                return Node('IntegerConstant', [], res, lineno=node.lineno)

        return node

    def fold_unary_op(self, node):
        child = node.children[0]
        op = node.leaf

        # CORREÇÃO: Usar 'IntegerConstant'
        if child.type == 'IntegerConstant' and op == 'MINUS':
            self.optimizations_count += 1
            return Node('IntegerConstant', [], -child.leaf, lineno=node.lineno)
        
        return node

    def fold_if_statement(self, node):
        cond = node.children[0]
        
        if cond.type == 'BooleanConstant':
            # .lower() para garantir que apanha 'True' ou 'true'
            val = str(cond.leaf).lower()
            
            if val == 'true':
                self.optimizations_count += 1
                return node.children[1] # Retorna só o THEN
            elif val == 'false':
                self.optimizations_count += 1
                if len(node.children) > 2:
                    return node.children[2] # Retorna só o ELSE
                else:
                    return Node('Empty', [], lineno=node.lineno) # Remove tudo
                    
        return node