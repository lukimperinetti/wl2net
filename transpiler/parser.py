"""Analyseur syntaxique (parser) : tokens WLangage -> AST.

Approche descente recursive. Les NEWLINE separent les instructions.
Le `=` est traite comme affectation au niveau instruction et comme egalite
dans les expressions de condition.
"""

from .lexer import Lexer
from . import ast_nodes as A

# Mots-cles de type -> type WL canonique
TYPE_KW = {
    "int": "int", "integer": "int", "entier": "int",
    "real": "real", "reel": "real",
    "string": "string", "chaine": "string",
    "boolean": "boolean", "booleen": "boolean", "bool": "boolean",
    "currency": "currency", "monetaire": "currency",
    "date": "date", "datetime": "datetime",
    "time": "time", "heure": "time",
    "buffer": "buffer", "variant": "variant",
}

LOGICAL = {"and": "&&", "et": "&&", "or": "||", "ou": "||"}
NOT_KW = {"not", "non"}
TRUE_KW = {"true", "vrai"}
FALSE_KW = {"false", "faux"}
NULL_KW = {"null", "nul"}


class Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.pos = 0

    # ---- utilitaires ------------------------------------------------------

    @property
    def cur(self):
        return self.toks[self.pos]

    def peek(self, k=1):
        j = self.pos + k
        return self.toks[j] if j < len(self.toks) else self.toks[-1]

    def advance(self):
        t = self.toks[self.pos]
        if self.pos < len(self.toks) - 1:
            self.pos += 1
        return t

    def error(self, msg):
        t = self.cur
        raise SyntaxError(f"Parser L{t.line}: {msg} (vu: {t.type} {t.value!r})")

    def is_kw(self, *norms):
        return self.cur.type == "KEYWORD" and self.cur.norm in norms

    def is_op(self, *vals):
        return self.cur.type == "OP" and self.cur.norm in vals

    def eat_kw(self, *norms):
        if not self.is_kw(*norms):
            self.error(f"mot-cle attendu {norms}")
        return self.advance()

    def eat_op(self, *vals):
        if not self.is_op(*vals):
            self.error(f"operateur attendu {vals}")
        return self.advance()

    def skip_newlines(self):
        while self.cur.type in ("NEWLINE", "COMMENT") and self.cur.type != "EOF":
            if self.cur.type == "COMMENT":
                return  # on laisse le commentaire etre traite comme instruction
            self.advance()

    def end_of_stmt(self):
        """Consomme la fin d'instruction (NEWLINE ou EOF)."""
        if self.cur.type == "NEWLINE":
            self.advance()
        elif self.cur.type == "EOF":
            pass

    # ---- point d'entree ---------------------------------------------------

    def parse_program(self):
        body = []
        while self.cur.type != "EOF":
            if self.cur.type == "NEWLINE":
                self.advance()
                continue
            body.append(self.parse_statement())
        return A.Program(body)

    def parse_block(self, *terminators):
        """Parse des instructions jusqu'a un mot-cle terminateur (ex: end, else)."""
        body = []
        while True:
            while self.cur.type == "NEWLINE":
                self.advance()
            if self.cur.type == "EOF":
                break
            if self.cur.type == "KEYWORD" and self.cur.norm in terminators:
                break
            body.append(self.parse_statement())
        return body

    # ---- instructions -----------------------------------------------------

    def parse_statement(self):
        t = self.cur

        if t.type == "COMMENT":
            self.advance()
            return A.Comment(t.value)

        if t.type == "KEYWORD":
            if t.norm in ("if", "si"):
                return self.parse_if()
            if t.norm in ("for", "pour"):
                return self.parse_for()
            if t.norm in ("while", "tantque", "tant"):
                return self.parse_while()
            if t.norm in ("loop", "boucle"):
                return self.parse_loop()
            if t.norm in ("switch", "selon"):
                return self.parse_switch()
            if t.norm in ("procedure", "proc", "function", "fonction"):
                return self.parse_procedure()
            if t.norm in ("return", "renvoyer", "retour", "retourner", "rendre"):
                return self.parse_return()
            if t.norm in ("break", "sortir"):
                self.advance()
                self.end_of_stmt()
                return A.Break()
            if t.norm in ("continue", "continuer"):
                self.advance()
                self.end_of_stmt()
                return A.Continue()

        # Declaration de variable : IDENT (is|est ...) TYPE [= expr]
        if t.type == "IDENT" and self._looks_like_decl():
            return self.parse_var_decl()

        # Affectation ou appel
        return self.parse_assign_or_call()

    def _looks_like_decl(self):
        # IDENT suivi de 'is' / 'est'
        nxt = self.peek()
        return nxt.type == "KEYWORD" and nxt.norm in ("is", "are", "est", "sont")

    def parse_var_decl(self):
        name = self.advance().value
        # is / est [un/une/des]
        self.eat_kw("is", "are", "est", "sont")
        while self.is_kw("un", "une", "des"):
            self.advance()
        wl_type = None
        if self.cur.type == "KEYWORD" and self.cur.norm in TYPE_KW:
            wl_type = TYPE_KW[self.cur.norm]
            self.advance()
        elif self.cur.type == "IDENT":
            # type "objet" (classe, structure) : on garde le nom tel quel
            wl_type = self.advance().value
        init = None
        if self.is_op("="):
            self.advance()
            init = self.parse_expression()
        self.end_of_stmt()
        return A.VarDecl(name, wl_type, init)

    def parse_assign_or_call(self):
        # Parse une cible postfixee (ident, .membre, [index], appel) SANS '='
        target = self.parse_postfix()
        if self.is_op("="):
            self.advance()
            expr = self.parse_expression()
            self.end_of_stmt()
            return A.Assign(target, expr)
        self.end_of_stmt()
        return A.ExprStmt(target)

    def parse_if(self):
        self.eat_kw("if", "si")
        cond = self.parse_expression(in_condition=True)
        if self.is_kw("then", "alors"):
            self.advance()
        then_body = self.parse_block("else", "sinon", "end", "fin")
        else_body = None
        if self.is_kw("else", "sinon"):
            self.advance()
            # else if -> on imbrique
            if self.is_kw("if", "si"):
                else_body = [self.parse_if()]
                return A.If(cond, then_body, else_body)
            else_body = self.parse_block("end", "fin")
        self.eat_kw("end", "fin")
        self.end_of_stmt()
        return A.If(cond, then_body, else_body)

    def parse_for(self):
        self.eat_kw("for", "pour")
        # FOR EACH / POUR TOUT
        if self.is_kw("each", "tout"):
            self.advance()
            # optionnel : 'element'/'de'/'of'
            var = self.advance().value if self.cur.type == "IDENT" else "item"
            if self.is_kw("of", "de"):
                self.advance()
            collection = self.parse_expression()
            body = self.parse_block("end", "fin")
            self.eat_kw("end", "fin")
            self.end_of_stmt()
            return A.ForEach(var, collection, body)

        var = self.advance().value          # variable de boucle
        self.eat_op("=")
        start = self.parse_expression()
        self.eat_kw("to")
        end = self.parse_expression()
        step = None
        if self.is_kw("step", "pas"):
            self.advance()
            step = self.parse_expression()
        body = self.parse_block("end", "fin")
        self.eat_kw("end", "fin")
        self.end_of_stmt()
        return A.For(var, start, end, step, body)

    def parse_while(self):
        # TANTQUE ou TANT QUE
        self.advance()
        if self.is_kw("que"):
            self.advance()
        cond = self.parse_expression(in_condition=True)
        body = self.parse_block("end", "fin")
        self.eat_kw("end", "fin")
        self.end_of_stmt()
        return A.While(cond, body)

    def parse_loop(self):
        self.eat_kw("loop", "boucle")
        body = self.parse_block("end", "fin")
        self.eat_kw("end", "fin")
        self.end_of_stmt()
        return A.Loop(body)

    def parse_switch(self):
        self.eat_kw("switch", "selon")
        expr = self.parse_expression()
        while self.cur.type == "NEWLINE":
            self.advance()
        cases = []
        default = None
        while self.is_kw("case", "cas", "other", "autre"):
            if self.is_kw("other", "autre"):
                self.advance()
                if self.is_op(":"):
                    self.advance()
                default = self.parse_block("case", "cas", "other", "autre", "end", "fin")
                continue
            self.advance()  # case
            values = [self.parse_expression()]
            while self.is_op(","):
                self.advance()
                values.append(self.parse_expression())
            if self.is_op(":"):
                self.advance()
            body = self.parse_block("case", "cas", "other", "autre", "end", "fin")
            cases.append(A.Case(values, body))
        self.eat_kw("end", "fin")
        self.end_of_stmt()
        return A.Switch(expr, cases, default)

    def parse_procedure(self):
        self.advance()  # procedure / fonction
        name = self.advance().value
        params = []
        if self.is_op("("):
            self.advance()
            while not self.is_op(")"):
                pname = self.advance().value
                ptype = None
                if self.is_kw("is", "est"):
                    self.advance()
                    while self.is_kw("un", "une", "des"):
                        self.advance()
                    if self.cur.type == "KEYWORD" and self.cur.norm in TYPE_KW:
                        ptype = TYPE_KW[self.cur.norm]
                        self.advance()
                    elif self.cur.type == "IDENT":
                        ptype = self.advance().value
                params.append((pname, ptype))
                if self.is_op(","):
                    self.advance()
            self.eat_op(")")
        body = self.parse_block("end", "fin")
        self.eat_kw("end", "fin")
        self.end_of_stmt()
        return A.Procedure(name, params, body)

    def parse_return(self):
        self.advance()
        expr = None
        if self.cur.type not in ("NEWLINE", "EOF"):
            expr = self.parse_expression()
        self.end_of_stmt()
        return A.Return(expr)

    # ---- expressions (precedence climbing) --------------------------------

    def parse_expression(self, in_condition=False):
        return self.parse_or(in_condition)

    def parse_or(self, ic):
        left = self.parse_and(ic)
        while self.is_kw("or", "ou"):
            self.advance()
            right = self.parse_and(ic)
            left = A.Binary("||", left, right)
        return left

    def parse_and(self, ic):
        left = self.parse_compare(ic)
        while self.is_kw("and", "et"):
            self.advance()
            right = self.parse_compare(ic)
            left = A.Binary("&&", left, right)
        return left

    def parse_compare(self, ic):
        left = self.parse_add(ic)
        while True:
            if self.is_op("<>"):
                self.advance(); left = A.Binary("!=", left, self.parse_add(ic))
            elif self.is_op("=="):
                self.advance(); left = A.Binary("==", left, self.parse_add(ic))
            elif self.is_op("="):
                # '=' est une egalite en contexte de condition
                self.advance(); left = A.Binary("==", left, self.parse_add(ic))
            elif self.is_op("<="):
                self.advance(); left = A.Binary("<=", left, self.parse_add(ic))
            elif self.is_op(">="):
                self.advance(); left = A.Binary(">=", left, self.parse_add(ic))
            elif self.is_op("<"):
                self.advance(); left = A.Binary("<", left, self.parse_add(ic))
            elif self.is_op(">"):
                self.advance(); left = A.Binary(">", left, self.parse_add(ic))
            else:
                break
        return left

    def parse_add(self, ic):
        left = self.parse_mul(ic)
        while self.is_op("+", "-"):
            op = self.advance().value
            left = A.Binary(op, left, self.parse_mul(ic))
        return left

    def parse_mul(self, ic):
        left = self.parse_unary(ic)
        while self.is_op("*", "/", "%"):
            op = self.advance().value
            left = A.Binary(op, left, self.parse_unary(ic))
        return left

    def parse_unary(self, ic):
        if self.is_kw(*NOT_KW):
            self.advance()
            return A.Unary("!", self.parse_unary(ic))
        if self.is_op("-", "+"):
            op = self.advance().value
            return A.Unary(op, self.parse_unary(ic))
        return self.parse_postfix()

    def parse_postfix(self):
        node = self.parse_primary()
        while True:
            if self.is_op("."):
                self.advance()
                name = self.advance().value
                # appel de methode ?
                if self.is_op("("):
                    args = self.parse_args()
                    node = A.Member(node, name)
                    node = A.Call("__method__", [node] + args)  # marqueur methode
                else:
                    node = A.Member(node, name)
            elif self.is_op("["):
                self.advance()
                idx = self.parse_expression()
                self.eat_op("]")
                node = A.Index(node, idx)
            else:
                break
        return node

    def parse_args(self):
        self.eat_op("(")
        args = []
        while not self.is_op(")"):
            args.append(self.parse_expression())
            if self.is_op(","):
                self.advance()
        self.eat_op(")")
        return args

    def parse_primary(self):
        t = self.cur
        if t.type == "NUMBER":
            self.advance()
            if "." in t.value:
                return A.Literal(float(t.value), t.value, "real")
            return A.Literal(int(t.value), t.value, "int")
        if t.type == "STRING":
            self.advance()
            return A.Literal(t.value, t.value, "string")
        if t.type == "KEYWORD" and t.norm in TRUE_KW:
            self.advance(); return A.Literal(True, t.value, "bool")
        if t.type == "KEYWORD" and t.norm in FALSE_KW:
            self.advance(); return A.Literal(False, t.value, "bool")
        if t.type == "KEYWORD" and t.norm in NULL_KW:
            self.advance(); return A.Literal(None, t.value, "null")
        if t.type == "IDENT":
            name = self.advance().value
            if self.is_op("("):
                args = self.parse_args()
                return A.Call(name, args)
            return A.Ident(name)
        if self.is_op("("):
            self.advance()
            e = self.parse_expression()
            self.eat_op(")")
            return e
        self.error("expression attendue")


def parse_source(src: str) -> A.Program:
    tokens = Lexer(src).tokenize()
    return Parser(tokens).parse_program()
