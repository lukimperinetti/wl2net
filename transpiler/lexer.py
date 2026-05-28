"""Analyseur lexical (lexer) pour le WLangage.

Le WLangage est insensible a la casse pour les mots-cles. Les retours a la
ligne sont significatifs (separateurs d'instructions). Les commentaires en
debut de ligne sont conserves (transmis comme tokens COMMENT) pour pouvoir
les reinjecter dans le C# genere.
"""

import unicodedata

# Mots-cles reconnus, normalises sans accents et en minuscules.
KEYWORDS = {
    # declaration
    "is", "are", "est", "sont", "un", "une", "des",
    # types
    "int", "integer", "entier", "real", "reel", "string", "chaine",
    "boolean", "booleen", "bool", "currency", "monetaire", "date",
    "time", "heure", "datetime", "buffer", "variant",
    # structures de controle
    "if", "si", "then", "alors", "else", "sinon", "end", "fin",
    "for", "pour", "to", "step", "pas", "each", "tout", "of", "de",
    "while", "tantque", "tant", "que", "loop", "boucle",
    "switch", "selon", "case", "cas", "other", "autre",
    "procedure", "proc", "function", "fonction",
    "return", "renvoyer", "retour", "retourner", "rendre",
    "break", "sortir", "continue", "continuer",
    # operateurs logiques / litteraux
    "and", "et", "or", "ou", "not", "non", "pas_logique",
    "true", "vrai", "false", "faux", "null", "nul",
}

# Operateurs multi-caracteres (a tester avant les simples).
MULTI_OPS = ["<>", "<=", ">=", "==", "->", "_to_"]
SINGLE_OPS = set("=<>+-*/%(),.[]:")


def _norm(s: str) -> str:
    """Minuscule + suppression des accents pour comparer les mots-cles."""
    s = s.lower()
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


class Token:
    __slots__ = ("type", "value", "norm", "line")

    def __init__(self, type_, value, line, norm=None):
        self.type = type_          # IDENT, NUMBER, STRING, KEYWORD, OP, NEWLINE, COMMENT, EOF
        self.value = value         # texte d'origine
        self.norm = norm           # forme normalisee (pour KEYWORD/OP)
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, L{self.line})"


class Lexer:
    def __init__(self, src: str):
        self.src = src.replace("\r\n", "\n").replace("\r", "\n")
        self.i = 0
        self.line = 1
        self.tokens = []

    def error(self, msg):
        raise SyntaxError(f"Lexer L{self.line}: {msg}")

    def tokenize(self):
        s = self.src
        n = len(s)
        while self.i < n:
            c = s[self.i]

            # Retour a la ligne
            if c == "\n":
                self._emit("NEWLINE", "\n")
                self.i += 1
                self.line += 1
                continue

            # Espaces / tabulations
            if c in " \t":
                self.i += 1
                continue

            # Commentaires // ...
            if c == "/" and self.i + 1 < n and s[self.i + 1] == "/":
                j = self.i + 2
                while j < n and s[j] != "\n":
                    j += 1
                text = s[self.i + 2:j].strip()
                self._emit("COMMENT", text)
                self.i = j
                continue

            # Chaines "..." (gestion du doublement "" comme guillemet)
            if c == '"':
                self.i += 1
                buf = []
                while self.i < n:
                    ch = s[self.i]
                    if ch == '"':
                        if self.i + 1 < n and s[self.i + 1] == '"':
                            buf.append('"')
                            self.i += 2
                            continue
                        self.i += 1
                        break
                    if ch == "\n":
                        self.error("chaine non terminee")
                    buf.append(ch)
                    self.i += 1
                self._emit("STRING", "".join(buf))
                continue

            # Nombres
            if c.isdigit() or (c == "." and self.i + 1 < n and s[self.i + 1].isdigit()):
                j = self.i
                seen_dot = False
                while j < n and (s[j].isdigit() or (s[j] == "." and not seen_dot)):
                    if s[j] == ".":
                        seen_dot = True
                    j += 1
                self._emit("NUMBER", s[self.i:j])
                self.i = j
                continue

            # Identifiants / mots-cles
            if c.isalpha() or c == "_":
                j = self.i
                while j < n and (s[j].isalnum() or s[j] == "_"):
                    j += 1
                word = s[self.i:j]
                nrm = _norm(word)
                # forme soulignee des mots-cles (ex: _TO_ -> to)
                stripped = nrm.strip("_")
                if nrm in KEYWORDS:
                    self._emit("KEYWORD", word, nrm)
                elif stripped in KEYWORDS and ("_" in word):
                    self._emit("KEYWORD", word, stripped)
                else:
                    self._emit("IDENT", word)
                self.i = j
                continue

            # Operateurs multi-caracteres
            matched = False
            for op in MULTI_OPS:
                if s[self.i:self.i + len(op)].lower() == op:
                    self._emit("OP", s[self.i:self.i + len(op)], op)
                    self.i += len(op)
                    matched = True
                    break
            if matched:
                continue

            # Operateurs simples
            if c in SINGLE_OPS:
                self._emit("OP", c, c)
                self.i += 1
                continue

            self.error(f"caractere inattendu {c!r}")

        self._emit("NEWLINE", "\n")
        self._emit("EOF", "")
        return self.tokens

    def _emit(self, type_, value, norm=None):
        self.tokens.append(Token(type_, value, self.line, norm))
