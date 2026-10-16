# -*- coding: utf-8 -*-
"""Banc d'essai : exerce la logique pure de l'App Module sans NVDA.

NVDA n'est pas importable hors de son propre environnement : ses modules sont
donc remplacés par des doublures, et l'App Module est exercé sur des objets
factices reproduisant la géométrie et les états réellement relevés dans
Wireshark 4.6.8. Le banc ne couvre que ce qui ne dépend pas de NVDA lui-même :
découpage des lignes, appariement des en-têtes, lecture de l'état de la
capture, masquage des données de capture.

Lancement :  python tests/test_wireshark.py
"""
import builtins, enum, sys, types
from pathlib import Path

# Ne jamais déposer de bytecode à côté du module : il se retrouverait dans le
# paquet de l'extension, compilé pour la version de Python du poste de travail
# et non pour celle de NVDA.
sys.dont_write_bytecode = True

builtins._ = lambda text: text

class Role(enum.IntEnum):
    UNKNOWN=0; WINDOW=1; PANE=3; STATICTEXT=7; BUTTON=9; MENUITEM=11
    COMBOBOX=13; LIST=14; LISTITEM=15; LINK=19; TREEVIEW=20; TREEVIEWITEM=21
    TABCONTROL=23; SCROLLBAR=26; FRAME=34; TOOLBAR=35; DROPDOWNBUTTON=36
    GROUPING=56; PROPERTYPAGE=57; CHECKBOX=5; CHECKMENUITEM=60
    MENUBAR=10; POPUPMENU=12; HEADER=70
class State(enum.IntEnum):
    UNAVAILABLE=1; FOCUSED=2; SELECTED=4; CHECKED=32; COLLAPSED=512
    SELECTABLE=8388608; FOCUSABLE=16777216; CHECKABLE=134217728
class OutputReason(enum.IntEnum):
    FOCUS=0

ct = types.ModuleType("controlTypes"); ct.Role=Role; ct.State=State; ct.OutputReason=OutputReason
class _UIA:
    presType_content = "content"
    def _get_name(self): return getattr(self, "_name", "")
    def _get_rowNumber(self): return getattr(self, "_rowNumber", 0)
    def _get_columnNumber(self): return 1
    def _get_table(self): return None
    def _get_description(self): return getattr(self, "_description", "")
uia_mod = types.ModuleType("NVDAObjects.UIA"); uia_mod.UIA = _UIA
nvdaobjects = types.ModuleType("NVDAObjects"); nvdaobjects.UIA = uia_mod
addonh = types.ModuleType("addonHandler")
addonh.initTranslation = lambda: None
appmod = types.ModuleType("appModuleHandler")
class _AppModule:
    processID = 42
appmod.AppModule = _AppModule
sh = types.ModuleType("scriptHandler"); sh.script = lambda **kw: (lambda f: f)
lh = types.ModuleType("logHandler")
lh.log = types.SimpleNamespace(info=lambda *a, **k: None, error=lambda *a, **k: None)
for name, mod in {
    "addonHandler": addonh,
    "api": types.ModuleType("api"), "appModuleHandler": appmod, "controlTypes": ct,
    "core": types.ModuleType("core"), "speech": types.ModuleType("speech"),
    "ui": types.ModuleType("ui"), "logHandler": lh, "scriptHandler": sh,
    "NVDAObjects": nvdaobjects, "NVDAObjects.UIA": uia_mod,
}.items():
    sys.modules[name] = mod

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "addon" / "appModules"))
import wireshark as w

class Rect:
    def __init__(self, left, top, width=10, height=24):
        self.left, self.top, self.width, self.height = left, top, width, height
class Cell:
    """Cellule factice : géométrie, nom UIA brut, rôle, états."""
    def __init__(self, name, left, top, role=Role.TREEVIEWITEM, states=None, autoId=""):
        self._n, self.location, self.role = name, Rect(left, top), role
        self.states = states or set()
        self.UIAElement = types.SimpleNamespace(
            CurrentName=name, CurrentAutomationId=autoId, CurrentClassName="")
        self.previous = self.next = self.parent = None

def chain(cells):
    for a, b in zip(cells, cells[1:]):
        a.next, b.previous = b, a
    return cells

failures = []
def check(label, got, expected):
    ok = got == expected
    print(("  OK   " if ok else "  ECHEC") + " " + label)
    if not ok:
        print("         attendu : %r" % (expected,)); print("         obtenu  : %r" % (got,))
        failures.append(label)

print("_rowCells — ligne de 7 colonnes, en-têtes au-dessus, ligne suivante en dessous")
headers = [Cell(n, i*100, 157, Role.HEADER) for i, n in enumerate(
    ["No.", "Time", "Source", "Destination", "Protocol", "Length", "Info"])]
row1 = [Cell(n, i*100, 190) for i, n in enumerate(
    ["1", "0.000000000", "192.168.1.138", "52.112.100.51", "TLSv1.2", "104", "Application Data"])]
row2 = [Cell(n, i*100, 214) for i, n in enumerate(["2", "0.006190900", "", "", "TCP", "54", "ACK"])]
chain(headers + row1 + row2)
check("depuis la colonne 0", [c._n for c in w._rowCells(row1[0])], [c._n for c in row1])
check("depuis une colonne du milieu", [c._n for c in w._rowCells(row1[3])], [c._n for c in row1])
check("depuis la dernière colonne", [c._n for c in w._rowCells(row1[6])], [c._n for c in row1])

print("_columnHeaders — les en-têtes, et rien qu'eux")
view = types.SimpleNamespace(firstChild=headers[0])
check("sept en-têtes", w._columnHeaders(view), ["No.","Time","Source","Destination","Protocol","Length","Info"])
check("vue absente", w._columnHeaders(None), [])

print("_describeRow — chaque valeur avec son libellé, colonnes vides omises")
for c in row1 + row2: c.parent = view
check("ligne complète", w._describeRow(row1[0]),
      "No. 1, Time 0.000000000, Source 192.168.1.138, Destination 52.112.100.51, "
      "Protocol TLSv1.2, Length 104, Info Application Data")
check("colonnes vides omises", w._describeRow(row2[0]),
      "No. 2, Time 0.006190900, Protocol TCP, Length 54, Info ACK")

print("_readCaptureState — relevé du 20 septembre")
def toolbar(startStates):
    start = Cell("Démarrer", 0, 0, Role.CHECKBOX, startStates)
    stop = Cell("Arrêter", 40, 0, Role.BUTTON, {State.UNAVAILABLE})
    return types.SimpleNamespace(children=[start, stop])
check("capture arrêtée", w._readCaptureState(toolbar({State.CHECKABLE})), False)
check("capture en cours", w._readCaptureState(
    toolbar({State.CHECKABLE, State.CHECKED, State.UNAVAILABLE})), True)
check("aucune commande cochable", w._readCaptureState(types.SimpleNamespace(children=[])), None)
check("barre illisible", w._readCaptureState(types.SimpleNamespace()), None)

print("_diag / _safeObject — le repli ne fabrique plus de texte")
def boom(): raise RuntimeError("bang")
check("_safeObject renvoie None", w._safeObject(boom), None)
check("le repli chaîne est bien vide", w._safeObject(boom) or "", "")
check("_diag décrit l'échec", w._diag(boom).startswith("<erreur> (RuntimeError"), True)

print("_holdsCaptureData — masquage des données de capture")
packetCell = Cell("trame 3, ACK", 0, 190, Role.TREEVIEWITEM, autoId="…splitterMaster.PacketList")
packetCell.parent = None
ifaceCell = Cell("Wi-Fi", 0, 190, Role.LISTITEM, autoId="…welcomePage.interfaceTree")
ifaceCell.parent = None
button = Cell("Démarrer", 0, 0, Role.BUTTON)
check("ligne de paquet masquée", w._holdsCaptureData(packetCell), True)
check("ligne d'interface en clair", w._holdsCaptureData(ifaceCell), False)
check("bouton en clair", w._holdsCaptureData(button), False)

print("ROW_ROLES — la commande de lecture accepte les deux rôles")
check("élément d'arborescence", Role.TREEVIEWITEM in w.ROW_ROLES, True)
check("élément de liste (interfaces)", Role.LISTITEM in w.ROW_ROLES, True)
check("bouton refusé", Role.BUTTON in w.ROW_ROLES, False)

print()
print("ECHECS : %d" % len(failures) if failures else "Tous les contrôles passent.")
sys.exit(1 if failures else 0)
