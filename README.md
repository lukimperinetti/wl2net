# [Vibe coding] - wl2net — Transpileur WLangage (WinDev/WebDev) → C# (.NET)

Outil en ligne de commande qui parse du code **WLangage exporté en texte** et
génère du **C# lisible et maintenable**. Conçu pour accélérer la migration de
la **logique métier / backend** d'un projet PCsoft vers .NET.

---

## ⚠️ À lire d'abord : ce que l'outil fait (et ne fait pas)

Soyons honnêtes, car aucun outil — même commercial — ne migre un projet
WinDev/WebDev intégralement et automatiquement.

**✅ Ce que wl2net fait bien (la partie tractable, ~70 % de l'effort) :**
- Transpile la **logique métier** : procédures, traitements, classes, calculs.
- Convertit les structures du langage (voir tableau plus bas).
- Mappe les fonctions WLangage courantes vers leurs équivalents .NET.
- Génère du C# propre, organisé en `namespace` + `class`, prêt à intégrer.

**❌ Ce que wl2net NE fait PAS (limites structurelles) :**
- **Le visuel (fenêtres WinDev, pages WebDev)** n'est *pas* reconstruit
  automatiquement. Ces éléments sont stockés dans des formats propriétaires
  binaires (`.wdw`, `.wwh`...) illisibles comme du texte. C'est le point dur de
  toute migration, et il demande un travail manuel ou semi-manuel (voir
  « Stratégie de migration » ci-dessous).
- **HFSQL** : les accès base (`HLitPremier`, `HAjoute`...) ne sont pas convertis
  en Entity Framework / ADO.NET — l'appel est conservé tel quel et signalé.
- Les **milliers de fonctions WLangage** ne sont pas toutes mappées : celles qui
  manquent sont conservées telles quelles et listées en sortie pour que tu les
  ajoutes (c'est volontairement extensible).

Autrement dit : wl2net te fait gagner l'essentiel du temps sur le backend, te
laisse une liste claire de ce qui reste à traiter, et ne prétend pas faire de
magie sur l'UI.

---

## Installation

Aucune dépendance externe — Python 3.8+ suffit.

```bash
cd wl2net
python3 wd2net.py examples/facture.wl
```

## Utilisation

```bash
# Transpiler un fichier vers la sortie standard
python3 wd2net.py mon_traitement.wl

# Vers un fichier .cs
python3 wd2net.py mon_traitement.wl -o Migration/MonTraitement.cs

# Tout un dossier de sources (.wl / .txt) -> dossier _cs/
python3 wd2net.py src_wlangage/ -o src_csharp/

# Changer le namespace généré
python3 wd2net.py mon_traitement.wl -n MaSociete.Migration
```

### Comment exporter le code WLangage depuis WinDev/WebDev

L'outil attend du **texte**, pas les fichiers projet binaires. Pour l'obtenir :
1. Dans l'éditeur de code, sélectionne le traitement / la collection de
   procédures → clic droit → **Copier le code** (ou « Exporter »).
2. Colle dans un fichier `.wl` (ou `.txt`).
3. Pour traiter beaucoup de fichiers, exporte le projet et récupère les
   sources textuelles, puis lance wl2net sur le dossier.

---

## Fonctionnalités du langage prises en charge

| WLangage | C# généré | FR + EN |
|---|---|---|
| `n is int`, `n est un entier` | `int n = 0;` | ✅ |
| `s is string = "x"` | `string s = "x";` | ✅ |
| `IF/THEN/ELSE/END`, `SI/ALORS/SINON/FIN` | `if/else { }` | ✅ |
| `else if` imbriqué | `else if { }` | ✅ |
| `FOR i = 1 TO n [STEP k]`, `POUR` | `for (...)` | ✅ |
| `FOR EACH x OF coll`, `POUR TOUT` | `foreach (...)` | ✅ |
| `WHILE`, `TANTQUE` | `while (...)` | ✅ |
| `LOOP`, `BOUCLE` | `while (true)` | ✅ |
| `SWITCH/CASE/OTHER`, `SELON/CAS/AUTRE` | `switch/case/default` | ✅ |
| `PROCEDURE`, `FONCTION` (+ inférence du type de retour) | `public static` | ✅ |
| `RETURN`, `RENVOYER`, `RETOUR` | `return` | ✅ |
| `BREAK/SORTIR`, `CONTINUE/CONTINUER` | `break` / `continue` | ✅ |
| `=` (en condition) / `<>` | `==` / `!=` | ✅ |
| `AND/OR/NOT`, `ET/OU/NON` | `&&` / `\|\|` / `!` | ✅ |
| Appels de méthode `obj.Methode(...)` | idem | ✅ |
| Commentaires `//` en début de ligne | `//` conservés | ✅ |
| Fonctions chaînes/maths/dates courantes | équivalents .NET | ✅ |

Le `=` est interprété comme **affectation** en position d'instruction et comme
**égalité** dans les conditions (comportement WLangage natif).

---

## Étendre l'outil (fonctions non mappées)

Quand wl2net rencontre une fonction WLangage inconnue, il **conserve l'appel
tel quel** et le **liste en fin d'exécution**. Pour la mapper, ajoute une ligne
dans `transpiler/mappings.py`, dictionnaire `FUNCTIONS` (clé = nom normalisé en
minuscules, sans accent) :

```python
FUNCTIONS = {
    # ...
    "dateversentier": lambda a: f"int.Parse({a[0]}.ToString(\"yyyyMMdd\"))",
    "hlitpremier":    lambda a: f"/* TODO HFSQL */ {a[0]}.First()",
}
```

Le `lambda` reçoit la liste des arguments **déjà transpilés** (chaînes C#) et
renvoie l'expression C#.

---

## Stratégie de migration recommandée (vue d'ensemble)

wl2net traite le backend. Pour le reste, voici l'approche réaliste :

1. **Backend / logique métier** → wl2net (ce dépôt). Relire et compléter les
   appels signalés.
2. **Base de données HFSQL** → migrer le schéma vers SQL Server / PostgreSQL,
   puis remplacer les accès `Hxxx` par Entity Framework Core. À mapper au cas
   par cas dans `mappings.py` ou à réécrire.
3. **Interface utilisateur** — choisir une cible .NET selon le projet :
   - WinDev (desktop) → **WPF** (moderne) ou **WinForms** (proche structurellement).
   - WebDev (web) → **Blazor** ou **ASP.NET Core MVC** ; le HTML/CSS des pages
     WebDev récentes est plus récupérable que les fenêtres WinDev binaires.
   - La reconstruction visuelle reste majoritairement **manuelle** ou assistée :
     wl2net ne génère pas l'UI.
4. **Tests** : générer des tests sur les procédures transpilées pour valider
   l'équivalence de comportement avant de basculer.

---

## Limites connues / pistes d'amélioration

- Pas d'analyse sémantique poussée : l'inférence de type de retour est
  heuristique (sinon `object` ou `void`).
- Pas de gestion des structures (`STRUCTURE`), tableaux associatifs, et types
  composés avancés (extensible).
- Pas de conversion HFSQL → EF Core (à ajouter dans les mappings).
- Pas de reconstruction de l'UI (limite structurelle assumée).

C'est un socle solide et extensible, pas une boîte noire : tout est lisible et
modifiable.
