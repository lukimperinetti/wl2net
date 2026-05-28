"""Generation de code C# a partir de l'AST."""

import unicodedata
from . import ast_nodes as A
from .mappings import FUNCTIONS, cs_type, cs_default


def _norm(s):
    s = s.lower()
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


class CodeGen:
    def __init__(self, class_name="Programme", namespace="MigrationWinDev"):
        self.class_name = class_name
        self.namespace = namespace
        self.lines = []
        self.indent = 0
        # suivi des types de variables locales pour inferer le type de retour
        self.var_types = {}
        self.unmapped = set()
        self.known_procs = set()    # procedures definies par l'utilisateur

    # ---- helpers ----------------------------------------------------------

    def w(self, line=""):
        self.lines.append("    " * self.indent + line if line else "")

    def emit_body(self, body):
        for stmt in body:
            self.emit_stmt(stmt)

    # ---- programme --------------------------------------------------------

    def generate(self, prog: A.Program) -> str:
        globals_, procs, others = [], [], []
        for s in prog.body:
            if isinstance(s, A.Procedure):
                procs.append(s)
            elif isinstance(s, (A.VarDecl,)):
                globals_.append(s)
            else:
                others.append(s)

        self.known_procs = {p.name for p in procs}

        self.w("// Genere automatiquement par wl2net (WLangage -> C#)")
        self.w("// Verifie les blocs marques TODO : conversion partielle.")
        self.w("using System;")
        self.w("using System.Collections.Generic;")
        self.w("using System.Linq;")
        self.w()
        self.w(f"namespace {self.namespace}")
        self.w("{")
        self.indent += 1
        self.w(f"public static class {self.class_name}")
        self.w("{")
        self.indent += 1

        # champs globaux
        for g in globals_:
            self.emit_field(g)
        if globals_:
            self.w()

        # procedures
        for i, p in enumerate(procs):
            self.emit_procedure(p)
            if i < len(procs) - 1:
                self.w()

        # instructions hors procedure -> Main()
        runnable = [s for s in others if not isinstance(s, A.Comment)]
        if runnable:
            if procs:
                self.w()
            self.w("public static void Main()")
            self.w("{")
            self.indent += 1
            self.emit_body(others)
            self.indent -= 1
            self.w("}")

        self.indent -= 1
        self.w("}")
        self.indent -= 1
        self.w("}")
        return "\n".join(self.lines) + "\n"

    # ---- declarations -----------------------------------------------------

    def emit_field(self, v: A.VarDecl):
        t = cs_type(v.wl_type)
        self.var_types[v.name] = t
        if v.init is not None:
            self.w(f"public static {t} {v.name} = {self.expr(v.init)};")
        else:
            self.w(f"public static {t} {v.name} = {cs_default(t)};")

    def emit_procedure(self, p: A.Procedure):
        saved = dict(self.var_types)
        params = []
        for name, wl in p.params:
            ct = cs_type(wl)
            self.var_types[name] = ct
            params.append(f"{ct} {name}")
        self._register_locals(p.body)        # pour l'inference du type de retour
        ret_type = self.infer_return_type(p)
        sig = f"public static {ret_type} {p.name}({', '.join(params)})"
        self.w(sig)
        self.w("{")
        self.indent += 1
        self.emit_body(p.body)
        self.indent -= 1
        self.w("}")
        self.var_types = saved

    def _register_locals(self, body):
        """Enregistre les types des variables locales (recursif) pour
        permettre l'inference du type de retour avant generation."""
        for s in body:
            if isinstance(s, A.VarDecl):
                self.var_types[s.name] = cs_type(s.wl_type)
            elif isinstance(s, A.For):
                self.var_types[s.var] = "int"
            for attr in ("then_body", "else_body", "body", "default"):
                sub = getattr(s, attr, None)
                if isinstance(sub, list):
                    self._register_locals(sub)
            if isinstance(s, A.Switch):
                for c in s.cases:
                    self._register_locals(c.body)

    def infer_return_type(self, p: A.Procedure):
        """Cherche un RETURN avec valeur et tente d'inferer son type."""
        rt = self._find_return_type(p.body)
        return rt or "void"

    def _find_return_type(self, body):
        for s in body:
            if isinstance(s, A.Return):
                if s.expr is None:
                    continue
                return self.expr_type(s.expr)
            for attr in ("then_body", "else_body", "body", "default"):
                sub = getattr(s, attr, None)
                if isinstance(sub, list):
                    t = self._find_return_type(sub)
                    if t:
                        return t
            if isinstance(s, A.Switch):
                for c in s.cases:
                    t = self._find_return_type(c.body)
                    if t:
                        return t
        return None

    def expr_type(self, e):
        if isinstance(e, A.Literal):
            return {"int": "int", "real": "double", "string": "string",
                    "bool": "bool"}.get(e.kind, "object")
        if isinstance(e, A.Ident):
            return self.var_types.get(e.name, "object")
        if isinstance(e, A.Binary):
            if e.op in ("==", "!=", "<", ">", "<=", ">=", "&&", "||"):
                return "bool"
            lt = self.expr_type(e.left)
            rt = self.expr_type(e.right)
            if "string" in (lt, rt):
                return "string"
            if "double" in (lt, rt):
                return "double"
            return lt if lt == rt else "object"
        return "object"

    # ---- instructions -----------------------------------------------------

    def emit_stmt(self, s):
        if isinstance(s, A.Comment):
            self.w(f"// {s.text}")
        elif isinstance(s, A.VarDecl):
            t = cs_type(s.wl_type)
            self.var_types[s.name] = t
            if s.init is not None:
                self.w(f"{t} {s.name} = {self.expr(s.init)};")
            else:
                self.w(f"{t} {s.name} = {cs_default(t)};")
        elif isinstance(s, A.Assign):
            self.w(f"{self.expr(s.target)} = {self.expr(s.expr)};")
        elif isinstance(s, A.ExprStmt):
            self.w(f"{self.expr(s.expr)};")
        elif isinstance(s, A.Return):
            if s.expr is None:
                self.w("return;")
            else:
                self.w(f"return {self.expr(s.expr)};")
        elif isinstance(s, A.Break):
            self.w("break;")
        elif isinstance(s, A.Continue):
            self.w("continue;")
        elif isinstance(s, A.If):
            self.emit_if(s)
        elif isinstance(s, A.For):
            self.emit_for(s)
        elif isinstance(s, A.ForEach):
            self.emit_foreach(s)
        elif isinstance(s, A.While):
            self.w(f"while ({self.expr(s.cond)})")
            self._block(s.body)
        elif isinstance(s, A.Loop):
            self.w("while (true)")
            self._block(s.body)
        elif isinstance(s, A.Switch):
            self.emit_switch(s)
        elif isinstance(s, A.Procedure):
            # procedure imbriquee -> fonction locale
            self.emit_procedure(s)
        else:
            self.w(f"// TODO: instruction non geree: {type(s).__name__}")

    def _block(self, body):
        self.w("{")
        self.indent += 1
        self.emit_body(body)
        self.indent -= 1
        self.w("}")

    def emit_if(self, s: A.If):
        self.w(f"if ({self.expr(s.cond)})")
        self._block(s.then_body)
        if s.else_body is not None:
            # else if ?
            if len(s.else_body) == 1 and isinstance(s.else_body[0], A.If):
                inner = s.else_body[0]
                self.w(f"else if ({self.expr(inner.cond)})")
                self._block(inner.then_body)
                if inner.else_body is not None:
                    self.w("else")
                    self._block(inner.else_body)
            else:
                self.w("else")
                self._block(s.else_body)

    def emit_for(self, s: A.For):
        self.var_types[s.var] = "int"
        if s.step is not None:
            step = self.expr(s.step)
            self.w(f"for (int {s.var} = {self.expr(s.start)}; "
                   f"{s.var} <= {self.expr(s.end)}; {s.var} += {step})")
        else:
            self.w(f"for (int {s.var} = {self.expr(s.start)}; "
                   f"{s.var} <= {self.expr(s.end)}; {s.var}++)")
        self._block(s.body)

    def emit_foreach(self, s: A.ForEach):
        self.var_types[s.var] = "var"
        self.w(f"foreach (var {s.var} in {self.expr(s.collection)})")
        self._block(s.body)

    def emit_switch(self, s: A.Switch):
        self.w(f"switch ({self.expr(s.expr)})")
        self.w("{")
        self.indent += 1
        for c in s.cases:
            for v in c.values:
                self.w(f"case {self.expr(v)}:")
            self.indent += 1
            self.emit_body(c.body)
            self.w("break;")
            self.indent -= 1
        if s.default is not None:
            self.w("default:")
            self.indent += 1
            self.emit_body(s.default)
            self.w("break;")
            self.indent -= 1
        self.indent -= 1
        self.w("}")

    # ---- expressions ------------------------------------------------------

    def expr(self, e) -> str:
        if isinstance(e, A.Literal):
            if e.kind == "string":
                escaped = e.value.replace("\\", "\\\\").replace('"', '\\"')
                return f'"{escaped}"'
            if e.kind == "bool":
                return "true" if e.value else "false"
            if e.kind == "null":
                return "null"
            return e.raw
        if isinstance(e, A.Ident):
            return e.name
        if isinstance(e, A.Unary):
            return f"{e.op}({self.expr(e.operand)})"
        if isinstance(e, A.Binary):
            return f"({self.expr(e.left)} {e.op} {self.expr(e.right)})"
        if isinstance(e, A.Member):
            return f"{self.expr(e.target)}.{e.name}"
        if isinstance(e, A.Index):
            return f"{self.expr(e.target)}[{self.expr(e.index)}]"
        if isinstance(e, A.Call):
            return self.emit_call(e)
        return f"/* expr? {type(e).__name__} */"

    def emit_call(self, c: A.Call) -> str:
        # appel de methode marque pendant le parsing
        if c.name == "__method__":
            member = c.args[0]            # A.Member
            args = [self.expr(a) for a in c.args[1:]]
            return f"{self.expr(member.target)}.{member.name}({', '.join(args)})"

        args = [self.expr(a) for a in c.args]
        key = _norm(c.name)
        if key in FUNCTIONS:
            return FUNCTIONS[key](args)
        # appel a une procedure utilisateur definie dans le meme fichier
        if c.name in self.known_procs:
            return f"{c.name}({', '.join(args)})"
        # fonction non mappee : on conserve l'appel + on signale
        self.unmapped.add(c.name)
        return f"{c.name}({', '.join(args)})"


def generate_csharp(prog: A.Program, class_name="Programme", namespace="MigrationWinDev"):
    g = CodeGen(class_name, namespace)
    code = g.generate(prog)
    return code, sorted(g.unmapped)
