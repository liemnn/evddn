import ast, operator, re

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.Gt: operator.gt,
    ast.Lt: operator.lt,
    ast.GtE: operator.ge,
    ast.LtE: operator.le,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}

def preprocess(expr: str) -> str:
    # chuẩn hóa toán tử logic về chữ thường
    expr = re.sub(r'\bAND\b', 'and', expr, flags=re.I)
    expr = re.sub(r'\bOR\b', 'or', expr, flags=re.I)
    expr = re.sub(r'\bNOT\b', 'not', expr, flags=re.I)
    return expr

def safe_eval_expr(expr, context):
    expr = preprocess(expr.strip())
    node = ast.parse(expr, mode='eval').body

    def _eval(n):
        if isinstance(n, ast.BinOp):
            return OPS[type(n.op)](_eval(n.left), _eval(n.right))
        elif isinstance(n, ast.Compare):
            left = _eval(n.left)
            for op, comp in zip(n.ops, n.comparators):
                right = _eval(comp)
                if not OPS[type(op)](left, right):
                    return False
                left = right
            return True
        elif isinstance(n, ast.BoolOp):
            if isinstance(n.op, ast.And):
                return all(_eval(v) for v in n.values)
            elif isinstance(n.op, ast.Or):
                return any(_eval(v) for v in n.values)
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -_eval(n.operand)
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            return not _eval(n.operand)
        elif isinstance(n, ast.Constant):
            return n.value
        elif isinstance(n, ast.Name):
            if n.id in context:
                return context[n.id]
            raise ValueError(f"Unknown variable {n.id}")
        else:
            raise ValueError(f"Unsupported expression: {ast.dump(n)}")
    return _eval(node)

def eval_formula(text, context):
    lines = [ln for ln in text.splitlines() if ln.strip()]
    for ln in lines:
        m = re.match(r'\s*if\s*(.+?)\s*(?:then\s*)?kq\s*=\s*(.+)', ln, flags=re.I)

        if m:
            cond, rhs = m.groups()
            if safe_eval_expr(cond, context):
                return safe_eval_expr(rhs, context)
            continue
        m = re.match(r'\s*else\s+if\s*(.+?)\s*(?:then\s*)?kq\s*=\s*(.+)', ln, flags=re.I)
        if m:
            cond, rhs = m.groups()
            if safe_eval_expr(cond, context):
                return safe_eval_expr(rhs, context)
            continue
        m = re.match(r'\s*else\s*(?:then\s*)?kq\s*=\s*(.+)', ln, flags=re.I)
        if m:
            rhs = m.group(1)
            return safe_eval_expr(rhs, context)
    return None

def extract_vars_from_expr(expr: str):
    expr = preprocess(expr.strip())
    node = ast.parse(expr, mode="eval")
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}

def get_vars(text: str):
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    vars_set = set()
    for ln in lines:
        m = re.match(r'\s*if\s*(.+?)\s*(?:then\s*)?kq=(.+)', ln, flags=re.I)
        if m:
            cond, rhs = m.groups()
            vars_set |= extract_vars_from_expr(cond)
            vars_set |= extract_vars_from_expr(rhs)
            continue
        m = re.match(r'\s*else\s+if\s*(.+?)\s*(?:then\s*)?kq=(.+)', ln, flags=re.I)
        if m:
            cond, rhs = m.groups()
            vars_set |= extract_vars_from_expr(cond)
            vars_set |= extract_vars_from_expr(rhs)
            continue
        m = re.match(r'\s*else\s*(?:then\s*)?kq=(.+)', ln, flags=re.I)
        if m:
            rhs = m.group(1)
            vars_set |= extract_vars_from_expr(rhs)
    return sorted(vars_set)


# Test
text = """
IF 3.1<1 KQ =((2.0*70000)+(1.0*100000)) 
ELSE KQ =((2.0*100000)+(1.0*150000))
"""
ctx = {'LCB':4000000}
print(eval_formula(text, ctx))   # -> 1000000
#print(get_vars(text))            # -> ['A', 'B', 'C']
