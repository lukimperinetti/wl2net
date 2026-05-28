"""Tables de correspondance WLangage -> C#.

C'est LE fichier a etendre quand le transpileur rencontre une fonction
WLangage non geree : ajoute une entree dans FUNCTIONS.
"""

# --- Types -----------------------------------------------------------------

TYPES = {
    "int": "int",
    "real": "double",
    "string": "string",
    "boolean": "bool",
    "currency": "decimal",
    "date": "DateTime",
    "datetime": "DateTime",
    "time": "TimeSpan",
    "buffer": "byte[]",
    "variant": "object",
}

DEFAULTS = {
    "int": "0",
    "double": "0",
    "string": '""',
    "bool": "false",
    "decimal": "0m",
    "DateTime": "DateTime.MinValue",
    "TimeSpan": "TimeSpan.Zero",
    "byte[]": "null",
    "object": "null",
}


def cs_type(wl_type):
    """Type WL -> type C#. Les types inconnus (classes) sont conserves."""
    if wl_type is None:
        return "object"
    return TYPES.get(wl_type, wl_type)


def cs_default(cs_t):
    return DEFAULTS.get(cs_t, "default")


# --- Fonctions integrees ---------------------------------------------------
# Chaque entree est une lambda recevant la liste des arguments deja transpiles
# (chaines C#) et renvoyant l'expression C#. La cle est normalisee (minuscule,
# sans accent) -- voir _norm dans le lexer.
#
# Rappel : le WLangage indexe les chaines a partir de 1.

def _arg(args, i, default="0"):
    return args[i] if i < len(args) else default


def _join_print(args):
    """Concatene les arguments d'un Trace/Info pour Console.WriteLine."""
    return " + ".join(args) if args else '""'


FUNCTIONS = {
    # --- Chaines ---
    "taille": lambda a: f"{_arg(a,0)}.Length",
    "length": lambda a: f"{_arg(a,0)}.Length",
    "gauche": lambda a: f"{_arg(a,0)}.Substring(0, {_arg(a,1)})",
    "left": lambda a: f"{_arg(a,0)}.Substring(0, {_arg(a,1)})",
    "droite": lambda a: f"{_arg(a,0)}.Substring({_arg(a,0)}.Length - {_arg(a,1)})",
    "right": lambda a: f"{_arg(a,0)}.Substring({_arg(a,0)}.Length - {_arg(a,1)})",
    "milieu": lambda a: f"{_arg(a,0)}.Substring(({_arg(a,1)}) - 1, {_arg(a,2)})",
    "middle": lambda a: f"{_arg(a,0)}.Substring(({_arg(a,1)}) - 1, {_arg(a,2)})",
    "majuscule": lambda a: f"{_arg(a,0)}.ToUpper()",
    "upper": lambda a: f"{_arg(a,0)}.ToUpper()",
    "minuscule": lambda a: f"{_arg(a,0)}.ToLower()",
    "lower": lambda a: f"{_arg(a,0)}.ToLower()",
    "sansespace": lambda a: f"{_arg(a,0)}.Trim()",
    "nospace": lambda a: f"{_arg(a,0)}.Trim()",
    "remplace": lambda a: f"{_arg(a,0)}.Replace({_arg(a,1)}, {_arg(a,2)})",
    "replace": lambda a: f"{_arg(a,0)}.Replace({_arg(a,1)}, {_arg(a,2)})",
    "position": lambda a: f"({_arg(a,0)}.IndexOf({_arg(a,1)}) + 1)",
    "contient": lambda a: f"{_arg(a,0)}.Contains({_arg(a,1)})",
    "commencepar": lambda a: f"{_arg(a,0)}.StartsWith({_arg(a,1)})",

    # --- Conversions ---
    "chaineversentier": lambda a: f"int.Parse({_arg(a,0)})",
    "stringtoint": lambda a: f"int.Parse({_arg(a,0)})",
    "entierverschaine": lambda a: f"{_arg(a,0)}.ToString()",
    "inttostring": lambda a: f"{_arg(a,0)}.ToString()",
    "val": lambda a: f"Convert.ToDouble({_arg(a,0)})",
    "numeriqueverschaine": lambda a: f"{_arg(a,0)}.ToString()",

    # --- Maths ---
    "abs": lambda a: f"Math.Abs({_arg(a,0)})",
    "arrondi": lambda a: f"Math.Round({_arg(a,0)}, {_arg(a,1,'0')})",
    "round": lambda a: f"Math.Round({_arg(a,0)}, {_arg(a,1,'0')})",
    "racine": lambda a: f"Math.Sqrt({_arg(a,0)})",
    "min": lambda a: f"Math.Min({_arg(a,0)}, {_arg(a,1)})",
    "max": lambda a: f"Math.Max({_arg(a,0)}, {_arg(a,1)})",
    "puissance": lambda a: f"Math.Pow({_arg(a,0)}, {_arg(a,1)})",

    # --- Dates ---
    "datedujour": lambda a: "DateTime.Today",
    "datesys": lambda a: "DateTime.Now",
    "now": lambda a: "DateTime.Now",
    "heuresys": lambda a: "DateTime.Now.TimeOfDay",

    # --- Affichage / debug ---
    "trace": lambda a: f"Console.WriteLine({_join_print(a)})",
    "info": lambda a: f"Console.WriteLine({_join_print(a)})",
    "erreur": lambda a: f"Console.Error.WriteLine({_join_print(a)})",
    "avertissement": lambda a: f"Console.WriteLine({_join_print(a)})",

    # --- Tableaux ---
    "tableauajoute": lambda a: f"{_arg(a,0)}.Add({_arg(a,1)})",
    "arrayadd": lambda a: f"{_arg(a,0)}.Add({_arg(a,1)})",
    "tableauoccurrence": lambda a: f"{_arg(a,0)}.Count",
    "arraycount": lambda a: f"{_arg(a,0)}.Count",
    "tableausupprimetout": lambda a: f"{_arg(a,0)}.Clear()",
}
