"""Transpileur WLangage (WinDev/WebDev) -> C# (.NET).

Usage rapide :
    from transpiler import transpile
    code, non_mappees = transpile(source_wlangage)
"""

from .parser import parse_source
from .codegen import generate_csharp


def transpile(src, class_name="Programme", namespace="MigrationWinDev"):
    """Transpile du code WLangage en C#.

    Renvoie (code_csharp, liste_fonctions_non_mappees).
    """
    prog = parse_source(src)
    return generate_csharp(prog, class_name, namespace)


__all__ = ["transpile", "parse_source", "generate_csharp"]
