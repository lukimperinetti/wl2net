#!/usr/bin/env python3
"""wl2net - Transpileur WLangage (WinDev/WebDev) vers C# (.NET).

Usage :
    python wd2net.py fichier.wl                 # transpile vers stdout
    python wd2net.py fichier.wl -o sortie.cs    # transpile vers un fichier
    python wd2net.py dossier_src/ -o dossier_out/   # transpile un dossier

Le transpileur attend du code WLANGAGE EXPORTE EN TEXTE. Sous WinDev/WebDev,
exporter le code : clic droit sur un traitement/collection de procedures ->
"Copier le code" ou exporter le projet en .wdpackage et recuperer les sources.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transpiler import transpile


def _class_name_from_path(path):
    base = os.path.splitext(os.path.basename(path))[0]
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in base)
    if cleaned and cleaned[0].isdigit():
        cleaned = "C" + cleaned
    return cleaned or "Programme"


def transpile_file(in_path, out_path=None, namespace="MigrationWinDev"):
    with open(in_path, "r", encoding="utf-8") as f:
        src = f.read()
    class_name = _class_name_from_path(in_path)
    code, unmapped = transpile(src, class_name=class_name, namespace=namespace)

    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"[OK] {in_path} -> {out_path}")
    else:
        print(code)

    if unmapped:
        print(f"\n[!] Fonctions WLangage non mappees dans {os.path.basename(in_path)} "
              f"(appel conserve tel quel) :", file=sys.stderr)
        for name in unmapped:
            print(f"      - {name}", file=sys.stderr)
        print("    Ajoute-les dans transpiler/mappings.py (dict FUNCTIONS).",
              file=sys.stderr)
    return unmapped


def main():
    ap = argparse.ArgumentParser(description="Transpileur WLangage -> C#")
    ap.add_argument("input", help="fichier .wl ou dossier source")
    ap.add_argument("-o", "--output", help="fichier ou dossier de sortie")
    ap.add_argument("-n", "--namespace", default="MigrationWinDev",
                    help="namespace C# genere")
    args = ap.parse_args()

    if os.path.isdir(args.input):
        out_dir = args.output or (args.input.rstrip("/\\") + "_cs")
        all_unmapped = set()
        for root, _, files in os.walk(args.input):
            for fn in files:
                if fn.lower().endswith((".wl", ".txt", ".wd")):
                    src_path = os.path.join(root, fn)
                    rel = os.path.relpath(src_path, args.input)
                    dst = os.path.join(out_dir, os.path.splitext(rel)[0] + ".cs")
                    all_unmapped |= set(transpile_file(src_path, dst, args.namespace))
        print(f"\nTermine. {len(all_unmapped)} fonction(s) distincte(s) non mappee(s).")
    else:
        transpile_file(args.input, args.output, args.namespace)


if __name__ == "__main__":
    main()
