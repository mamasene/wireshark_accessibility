# -*- coding: utf-8 -*-
# App Module pour Wireshark (wireshark.exe)
# Projet : accessibilité de Wireshark avec NVDA
# Auteurs : Mama Sene, Emmanuel
# Licence : GNU General Public License version 2
#
# CORRECTIONS APPORTÉES
# ---------------------
# Wireshark expose son interface exclusivement par UI Automation, via Qt. Trois
# familles de défauts en découlent, toutes du même genre : l'information existe
# dans l'arbre d'accessibilité, mais pas là où NVDA la cherche.
#
#   - Les listes en colonnes — interfaces de capture, paquets — sont découpées
#     par Qt en une cellule par colonne, et le focus se pose sur une cellule
#     sans texte ou ne portant qu'un numéro. Le nom de la ligne est recomposé à
#     partir des cellules voisines.
#   - Les boutons sans nom accessible portent leur infobulle en description :
#     elle est promue en nom.
#   - Les étiquettes focalisables — les liens de la page d'accueil — sont
#     exposées comme du texte statique, que NVDA traite comme de la mise en
#     page : elles sont présentées comme des liens et annoncées explicitement.
#
# S'y ajoute l'annonce du démarrage et de l'arrêt de la capture, que Wireshark
# ne signale par aucun événement d'accessibilité.
#
# Principes de conception :
#   - les corrections d'annonce ne reposent sur aucun gestionnaire d'événement :
#     elles portent sur la donnée que NVDA lit, pas sur le moment où il la lit ;
#   - une seule touche est interceptée, Ctrl+E, et elle est transmise à
#     Wireshark avant tout autre traitement : flèches, Tabulation et Entrée lui
#     restent entièrement acquises ;
#   - une seule temporisation, celle qui suit Ctrl+E. Deux relevés ont établi
#     que Wireshark n'émet aucun événement au démarrage ni à l'arrêt de la
#     capture ; à défaut d'événement, l'état est relu à cadence fixe. Ce
#     contrôle démarre sur une action de l'utilisateur, s'arrête dès que l'état
#     a changé et expire au bout de sept secondes et demie. Rien ne tourne au
#     repos, et aucune autre correction n'attend ni ne scrute ;
#   - identification par des repères issus du code C++ de Wireshark
#     (identifiant d'automatisation, nom de classe Qt), donc indépendants de la
#     langue de l'interface ; l'état de la capture est lu comme un état, jamais
#     comme un libellé ;
#   - identification de la ligne par la géométrie, donc insensible au nombre de
#     colonnes, à leur ordre et à la reconstruction à chaud de la liste ;
#   - aucune annonce d'activité réseau : Wireshark n'expose aucune valeur
#     fiable pour le graphique d'activité, rien ne sera donc inventé. De même,
#     aucun état de capture n'est annoncé s'il n'est pas réellement exposé ;
#   - aucune donnée de capture dans le journal : le contenu des lignes de
#     paquets, des détails et des statistiques est masqué dans les relevés de
#     diagnostic, qui ne renseignent que sur la structure de l'interface ;
#   - les commandes de diagnostic ne sont associées à aucun raccourci par
#     défaut. Elles restent assignables dans NVDA, Préférences, Gestes de
#     commandes, catégorie « Wireshark » ;
#   - inspections réalisées uniquement via des API NVDA publiques.

import addonHandler
import api
import appModuleHandler
import controlTypes
import core
import speech
import ui
from logHandler import log
from NVDAObjects.UIA import UIA
from scriptHandler import script

# Sans cet appel, _() consulte le catalogue de traduction de NVDA et non celui
# de l'extension : les traductions livrées ici ne seraient jamais utilisées.
# Exigence du guide des développeurs de NVDA, section « Plugin Translation ».
# L'appel précède toute évaluation de _() : les descriptions de commandes sont
# évaluées à l'import, lors de la construction des décorateurs @script.
addonHandler.initTranslation()

#: Fin de l'identifiant d'automatisation de la liste des interfaces.
#: Vient du nom de l'objet C++ dans Wireshark, donc identique dans toutes les langues.
INTERFACE_TREE_ID_SUFFIX = "interfaceTree"

#: Nom de classe Qt du cadre contenant la liste, utilisé en repli si
#: l'identifiant d'automatisation venait à changer dans une version future.
INTERFACE_FRAME_CLASS_NAME = "InterfaceFrame"

#: Identifiant d'automatisation de la vue de la liste des paquets, et nom de
#: classe Qt correspondant. Les cellules portent un identifiant terminé par
#: « .PacketList ». Tous deux viennent du code C++ de Wireshark.
PACKET_LIST_ID = "Packet list"
PACKET_LIST_CLASS_NAME = "PacketList"

#: Nombre maximal de cellules parcourues de part et d'autre pour retrouver le
#: nom d'une ligne. Garde-fou contre toute hiérarchie inattendue.
#: La liste des paquets compte sept colonnes dans la disposition par défaut.
MAX_CELLS_PER_ROW = 12

#: Profondeur maximale de remontée dans les parents lors du repli d'identification.
MAX_PARENT_LOOKUP = 3

#: Remplace tout texte susceptible de porter des données de la capture dans les
#: relevés. Le projet s'interdit d'écrire adresses, ports et charges utiles dans
#: le journal, y compris lorsque l'utilisateur mène un diagnostic.
REDACTED = "<contenu de capture masqué>"

#: Préfixes des lignes de devInfo porteuses de texte, écartées lorsque l'objet
#: relève de la capture.
REDACTED_DEVINFO_PREFIXES = ("name:", "value:", "description:", "displayText:")

# Marqueurs des relevés de diagnostic dans le journal NVDA.
MARK_BEGIN = "=== WIRESHARK-DIAG DEBUT : {title} ==="
MARK_END = "=== WIRESHARK-DIAG FIN : {title} ==="

MAX_ANCESTORS = 8
MAX_CHILDREN = 25

#: Conteneurs dans lesquels le relevé des commandes descend. Les arborescences
#: en sont délibérément exclues : elles portent les données de la capture, que
#: le projet s'interdit d'écrire dans le journal.
CONTAINER_ROLES = frozenset(
	{
		controlTypes.Role.WINDOW,
		controlTypes.Role.PANE,
		controlTypes.Role.UNKNOWN,
		controlTypes.Role.GROUPING,
		controlTypes.Role.TOOLBAR,
		controlTypes.Role.FRAME,
		controlTypes.Role.PROPERTYPAGE,
		controlTypes.Role.MENUBAR,
		controlTypes.Role.POPUPMENU,
	}
)

#: Rôles des commandes relevées. Aucun ne porte de données réseau.
COMMAND_ROLES = frozenset(
	{
		controlTypes.Role.TOOLBAR,
		controlTypes.Role.BUTTON,
		controlTypes.Role.DROPDOWNBUTTON,
		controlTypes.Role.CHECKBOX,
		controlTypes.Role.MENUITEM,
		controlTypes.Role.CHECKMENUITEM,
	}
)

#: Rôles des lignes acceptées par la commande de lecture détaillée. Les cellules
#: Qt portent « élément d'arborescence » ; la liste des interfaces reçoit de ce
#: module le rôle « élément de liste », plus juste pour une liste plate.
ROW_ROLES = frozenset(
	{
		controlTypes.Role.TREEVIEWITEM,
		controlTypes.Role.LISTITEM,
	}
)

#: Garde-fous du parcours : ni la profondeur ni le nombre d'objets ne doivent
#: laisser la commande occuper durablement le fil principal de NVDA.
MAX_SCAN_DEPTH = 7
MAX_SCAN_OBJECTS = 400

#: Fin de l'identifiant d'automatisation de la barre d'outils principale.
#: Vient du nom de l'objet C++ dans Wireshark, donc identique dans toutes les
#: langues. La barre de filtrage porte un identifiant distinct.
MAIN_TOOLBAR_ID_SUFFIX = "mainToolBar"

#: Cadence et durée maximale du contrôle de l'état de la capture après Ctrl+E.
#: Trente contrôles à 250 ms couvrent sept secondes et demie : de quoi laisser
#: Wireshark ouvrir sa boîte « paquets non enregistrés », attendre la réponse de
#: l'utilisateur, puis démarrer. Chaque contrôle se réduit à la lecture des
#: états d'une barre d'outils déjà connue.
CAPTURE_CHECK_INTERVAL_MS = 250
CAPTURE_CHECK_ATTEMPTS = 30


def _diag(getter):
	"""Évalue une propriété pour un relevé, en décrivant l'échec plutôt qu'en le taisant.

	Réservée à la journalisation : la valeur de retour est destinée à être lue,
	jamais réutilisée comme donnée. Pour obtenir une valeur exploitable avec un
	repli, utiliser _safeObject().
	"""
	try:
		return getter()
	except Exception as exc:  # noqa: BLE001 - diagnostic volontairement permissif
		return f"<erreur> ({exc.__class__.__name__}: {exc})"


def _safeObject(getter):
	"""Évalue une propriété NVDA, en renvoyant None si elle n'est pas lisible.

	Convient partout où une valeur absente doit se traduire par un repli franc :
	objet, chaîne vide, liste vide.
	"""
	try:
		return getter()
	except Exception:  # noqa: BLE001
		return None


def _rawUIAName(obj):
	"""Retourne le nom brut exposé par UI Automation pour cet objet.

	On lit délibérément l'élément UIA plutôt que la propriété ``name`` de
	l'objet NVDA : les cellules voisines portent elles aussi notre classe de
	correction, et interroger leur ``name`` déclencherait une récursion.
	"""
	try:
		return obj.UIAElement.CurrentName or ""
	except Exception:  # noqa: BLE001
		return ""


def _uiaAutomationId(obj):
	"""Retourne l'identifiant d'automatisation UIA, ou une chaîne vide."""
	automationId = getattr(obj, "UIAAutomationId", None)
	if automationId:
		return automationId
	try:
		return obj.UIAElement.CurrentAutomationId or ""
	except Exception:  # noqa: BLE001
		return ""


def _uiaClassName(obj):
	"""Retourne le nom de classe Qt exposé par UI Automation, ou une chaîne vide."""
	try:
		return obj.UIAElement.CurrentClassName or ""
	except Exception:  # noqa: BLE001
		return ""


def _belongsToInterfaceTree(obj):
	"""Indique si cet objet fait partie de la liste des interfaces de capture.

	Premier critère, le moins coûteux : l'identifiant d'automatisation. Dans
	Wireshark 4.6, la vue et ses cellules portent le même identifiant, terminé
	par « interfaceTree ».

	Second critère, en repli : la présence du cadre « InterfaceFrame » parmi les
	ancêtres proches. Ces deux repères viennent du code source de Wireshark et
	ne dépendent donc pas de la langue de l'interface.
	"""
	if _uiaAutomationId(obj).endswith(INTERFACE_TREE_ID_SUFFIX):
		return True
	parent = _safeObject(lambda: obj.parent)
	level = 0
	while parent is not None and level < MAX_PARENT_LOOKUP:
		if _uiaClassName(parent) == INTERFACE_FRAME_CLASS_NAME:
			return True
		parent = _safeObject(lambda p=parent: p.parent)
		level += 1
	return False


def _belongsToPacketList(obj):
	"""Indique si cet objet fait partie de la liste des paquets.

	La vue porte l'identifiant d'automatisation « Packet list » et le nom de
	classe Qt « PacketList » ; ses cellules portent un identifiant terminé par
	« .PacketList ». Ces deux repères viennent du code source de Wireshark et
	sont donc indépendants de la langue de l'interface.
	"""
	automationId = _uiaAutomationId(obj)
	if automationId == PACKET_LIST_ID or automationId.endswith("." + PACKET_LIST_CLASS_NAME):
		return True
	if _uiaClassName(obj) == PACKET_LIST_CLASS_NAME:
		return True
	parent = _safeObject(lambda: obj.parent)
	level = 0
	while parent is not None and level < MAX_PARENT_LOOKUP:
		if _uiaClassName(parent) == PACKET_LIST_CLASS_NAME:
			return True
		parent = _safeObject(lambda p=parent: p.parent)
		level += 1
	return False


def _rowCells(cell):
	"""Retourne les cellules de la même ligne visuelle, de gauche à droite.

	Deux cellules appartiennent à la même ligne lorsqu'elles partagent la même
	coordonnée verticale. Ce critère est insensible au nombre de colonnes, à
	leur ordre, et au défilement horizontal de la vue — la liste des paquets est
	couramment défilée, la première colonne se retrouvant alors hors écran.
	"""
	location = _safeObject(lambda: cell.location)
	if location is None:
		return [cell]
	rowTop = location.top
	before = []
	sibling = _safeObject(lambda: cell.previous)
	steps = 0
	while sibling is not None and steps < MAX_CELLS_PER_ROW:
		siblingLocation = _safeObject(lambda s=sibling: s.location)
		if siblingLocation is None or siblingLocation.top != rowTop:
			break
		before.append(sibling)
		sibling = _safeObject(lambda s=sibling: s.previous)
		steps += 1
	before.reverse()
	after = []
	sibling = _safeObject(lambda: cell.next)
	steps = 0
	while sibling is not None and steps < MAX_CELLS_PER_ROW:
		siblingLocation = _safeObject(lambda s=sibling: s.location)
		if siblingLocation is None or siblingLocation.top != rowTop:
			break
		after.append(sibling)
		sibling = _safeObject(lambda s=sibling: s.next)
		steps += 1
	return before + [cell] + after


def _columnHeaders(view):
	"""Retourne les noms des en-têtes de colonne, dans l'ordre d'affichage.

	Les en-têtes sont les premiers enfants de la vue et portent le rôle
	« en-tête », relevé sur la colonne « Info ». Contrairement aux cellules,
	ils ne sont pas focalisables. Leurs libellés sont traduits par Wireshark :
	on les lit, on ne les présume pas.
	"""
	headers = []
	if view is None:
		return headers
	child = _safeObject(lambda: view.firstChild)
	steps = 0
	while child is not None and steps < MAX_CELLS_PER_ROW:
		if _safeObject(lambda c=child: c.role) != controlTypes.Role.HEADER:
			break
		headers.append(_rawUIAName(child))
		child = _safeObject(lambda c=child: c.next)
		steps += 1
	return headers


def _describeRow(cell):
	"""Compose la lecture détaillée d'une ligne : chaque valeur avec sa colonne.

	Les colonnes vides sont omises. Si les en-têtes ne correspondent pas au
	nombre de cellules relevées — en-têtes masqués, vue partiellement
	construite — les valeurs sont restituées sans libellé plutôt qu'avec un
	libellé faux.
	"""
	cells = _rowCells(cell)
	headers = _columnHeaders(_safeObject(lambda: cell.parent))
	if len(headers) != len(cells):
		headers = []
	parts = []
	for index, rowCell in enumerate(cells):
		value = _rawUIAName(rowCell)
		if not value:
			continue
		header = headers[index] if index < len(headers) else ""
		parts.append(f"{header} {value}" if header else value)
	return ", ".join(parts)


class PacketListRow(UIA):
	"""Ligne de la liste des paquets.

	Wireshark répartit chaque paquet sur sept colonnes et pose le focus sur la
	première, qui ne contient que le numéro du paquet : NVDA annonçait donc
	« 1 », « 2 », « 3 » et rien d'autre.

	L'annonce est complétée par la dernière colonne renseignée de la ligne —
	la colonne « Info » dans la disposition par défaut de Wireshark, celle qui
	porte la description du paquet. Le relevé a écarté les autres colonnes :
	l'horodatage, par exemple, est une décimale à neuf chiffres qu'une synthèse
	vocale énonce chiffre par chiffre, information coûteuse à l'oreille et
	rarement utile en parcourant la liste. Toutes les colonnes restent
	accessibles à la demande, par la commande de lecture détaillée de la ligne.

	L'état « réduit » exposé par Qt est délibérément conservé : il signale que
	la ligne porte une arborescence de détails, atteignable par Tabulation.

	Les propriétés de tableau sont laissées intactes : la liste des paquets est
	un véritable tableau, la navigation par tableau de NVDA doit donc continuer
	de fonctionner.
	"""

	def _nativeName(self):
		try:
			return super()._get_name() or ""
		except Exception:  # noqa: BLE001
			return _rawUIAName(self)

	def _get_name(self):
		nativeName = self._nativeName()
		parts = []
		if nativeName:
			if nativeName.isdigit():
				# La colonne du focus contient le numéro du paquet. On le
				# qualifie pour que l'annonce commence par un mot plutôt que
				# par un chiffre nu ; le test évite de mal nommer une colonne
				# dont l'utilisateur aurait changé l'ordre.
				# Translators: %s is the packet number in the packet list.
				parts.append(_("frame %s") % nativeName)
			else:
				parts.append(nativeName)
		summary = self._lastColumnText()
		if summary and summary != nativeName:
			parts.append(summary)
		return ", ".join(parts) or nativeName

	def _get_positionInfo(self):
		"""Annonce la position du paquet et le nombre total de lignes affichées."""
		try:
			rowNumber = super()._get_rowNumber()
		except Exception:  # noqa: BLE001
			return None
		if not rowNumber:
			return None
		positionInfo = {"indexInGroup": rowNumber}
		rowCount = _safeObject(lambda: self.parent.rowCount)
		if rowCount:
			positionInfo["similarItemsInGroup"] = rowCount
		return positionInfo

	def _lastColumnText(self):
		"""Retourne le texte de la dernière colonne renseignée après celle-ci."""
		cells = _rowCells(self)
		for cell in reversed(cells):
			if cell is self:
				break
			text = _rawUIAName(cell)
			if text:
				return text
		return ""


class SingleColumnTreeCell(UIA):
	"""Cellule d'une arborescence Qt ne comportant qu'une seule colonne.

	Qt expose chaque ligne de QTreeView comme une cellule de tableau, même
	lorsque l'arborescence n'a qu'une colonne. NVDA annonçait alors un numéro de
	ligne et un numéro de colonne dépourvus de sens — « ligne 1, colonne 1 » sur
	chaque champ de l'arborescence des détails du paquet.

	Le nombre de colonnes est mesuré sur la vue parente plutôt que déduit de
	l'identité de la vue : la correction vaut donc pour toute arborescence à une
	colonne de Wireshark, sans rien présumer de son nom. Si la propriété n'est
	pas exposée, le comportement d'origine est conservé.

	Le niveau de profondeur, lui, est laissé intact : dans l'arborescence des
	détails, il distingue un protocole de ses champs.
	"""

	def _isSingleColumn(self):
		columnCount = _safeObject(lambda: self.parent.columnCount)
		return columnCount is not None and columnCount <= 1

	def _get_rowNumber(self):
		if self._isSingleColumn():
			raise NotImplementedError
		return super()._get_rowNumber()

	def _get_columnNumber(self):
		if self._isSingleColumn():
			raise NotImplementedError
		return super()._get_columnNumber()

	def _get_table(self):
		if self._isSingleColumn():
			raise NotImplementedError
		return super()._get_table()


class InterfaceTreeCell(UIA):
	"""Cellule de la liste des interfaces de capture.

	Lorsque la cellule n'a pas de nom propre — cas de la colonne étroite qui
	reçoit le focus et de la colonne du graphique d'activité — le nom est repris
	de la cellule de la même ligne qui en possède un.
	"""

	def _get_name(self):
		try:
			nativeName = super()._get_name()
		except Exception:  # noqa: BLE001
			nativeName = _rawUIAName(self)
		if nativeName:
			return nativeName
		return self._findRowLabel() or nativeName

	def _get_role(self):
		# La liste est plate : « élément de liste » est plus juste à l'oreille
		# que « élément d'arborescence » annoncé par Qt.
		return controlTypes.Role.LISTITEM

	def _get_positionInfo(self):
		"""Annonce « 3 sur 15 » plutôt que « ligne 3, niveau 1 ».

		Qt expose ces cellules à la fois comme éléments d'arborescence et comme
		cellules de tableau. NVDA en tirait deux informations inutiles pour une
		liste plate : un numéro de ligne et un niveau de profondeur toujours
		égal à 1. On remplace l'ensemble par une position dans la liste, qui
		indique en outre le nombre total d'interfaces.
		"""
		try:
			# Le numéro de ligne natif reste la source la plus fiable ; on le lit
			# avant de le neutraliser pour l'annonce.
			rowNumber = super()._get_rowNumber()
		except Exception:  # noqa: BLE001
			return None
		if not rowNumber:
			return None
		positionInfo = {"indexInGroup": rowNumber}
		rowCount = _safeObject(lambda: self.parent.rowCount)
		if rowCount:
			positionInfo["similarItemsInGroup"] = rowCount
		return positionInfo

	# Les trois propriétés suivantes déclarent que cet objet n'est pas une
	# cellule de tableau, ce qui évite l'annonce d'une position en ligne et en
	# colonne dépourvue de sens ici. NotImplementedError est la convention NVDA
	# pour une propriété non applicable ; les appelants la gèrent.

	def _get_rowNumber(self):
		raise NotImplementedError

	def _get_columnNumber(self):
		raise NotImplementedError

	def _get_table(self):
		raise NotImplementedError

	def _findRowLabel(self):
		"""Cherche un nom parmi les autres cellules de la même ligne visuelle."""
		for cell in _rowCells(self):
			if cell is self:
				continue
			name = _rawUIAName(cell)
			if name:
				return name
		return None


class DescribedButton(UIA):
	"""Bouton dépourvu de nom accessible mais pourvu d'une description.

	Plusieurs boutons de Wireshark — le bouton signets du filtre de capture, par
	exemple — n'exposent aucun nom : NVDA annonce alors « bouton », sans plus.
	Leur infobulle, elle, est exposée en description et déjà traduite par
	Wireshark. On la promeut en nom, et on la retire de la description pour
	qu'elle ne soit pas prononcée deux fois.
	"""

	def _nativeName(self):
		try:
			return super()._get_name() or ""
		except Exception:  # noqa: BLE001
			return _rawUIAName(self)

	def _nativeDescription(self):
		try:
			return super()._get_description() or ""
		except Exception:  # noqa: BLE001
			return ""

	def _get_name(self):
		nativeName = self._nativeName()
		if nativeName:
			return nativeName
		return self._nativeDescription()

	def _get_description(self):
		if self._nativeName():
			# Le bouton a son propre nom : sa description garde tout son sens.
			return self._nativeDescription()
		# La description sert désormais de nom : ne pas la répéter.
		return ""


class FocusableLabel(UIA):
	"""Étiquette Qt qui reçoit le focus : en réalité un lien.

	Les liens de la section « Learn » de la page d'accueil — documentation,
	wiki, questions et réponses, listes de diffusion — sont des QLabel exposés
	comme du simple texte statique. Ils portent pourtant un nom, une
	description, et s'activent par Entrée. NVDA, qui traite le texte statique
	comme un élément de mise en page, ne les annonçait pas du tout.

	Une étiquette qui entre dans l'ordre de tabulation n'est jamais décorative :
	on la présente donc comme un lien, et on la déclare explicitement comme
	contenu à restituer.
	"""

	def _get_role(self):
		return controlTypes.Role.LINK

	def _get_presentationType(self):
		return self.presType_content


class InterfaceTreeList(UIA):
	"""Vue contenant la liste des interfaces de capture.

	Wireshark n'attribue pas de nom accessible à la vue elle-même, mais le cadre
	qui la contient en possède un, traduit. On le reprend afin que NVDA annonce
	la liste lorsque le focus y entre.
	"""

	def _get_name(self):
		try:
			nativeName = super()._get_name()
		except Exception:  # noqa: BLE001
			nativeName = _rawUIAName(self)
		if nativeName:
			return nativeName
		parent = _safeObject(lambda: self.parent)
		if parent is not None:
			return _rawUIAName(parent)
		return nativeName

	def _get_role(self):
		return controlTypes.Role.LIST


# -- État de la capture ---------------------------------------------------------


def _findMainToolBar(root):
	"""Retrouve la barre d'outils principale sous cette racine.

	Le repère est l'identifiant d'automatisation, issu du code C++ de
	Wireshark : il ne dépend ni de la langue ni de la position de la barre. Le
	parcours est borné en profondeur et en nombre d'objets, et ne descend que
	dans des conteneurs.
	"""
	queue = [(root, 0)]
	visited = 0
	while queue and visited < MAX_SCAN_OBJECTS:
		obj, depth = queue.pop(0)
		visited += 1
		if _uiaAutomationId(obj).endswith(MAIN_TOOLBAR_ID_SUFFIX):
			return obj
		role = _safeObject(lambda o=obj: o.role)
		if depth < MAX_SCAN_DEPTH and (depth == 0 or role in CONTAINER_ROLES):
			for child in _safeObject(lambda o=obj: o.children) or []:
				queue.append((child, depth + 1))
	return None


def _readCaptureState(toolBar):
	"""Indique si une capture est en cours, ou None si l'état n'est pas lisible.

	Wireshark n'annonce pas la capture par un texte exploitable : le titre de
	la fenêtre passe de « *Wi-Fi » à « Capturing from Wi-Fi », mais ce libellé
	dépendrait de la langue de l'interface. Le repère retenu est un **état**,
	donc structurel : dans la barre d'outils principale, la première commande
	cochable est l'action de capture, et elle est cochée pendant la capture.

	Relevé du 20 septembre 2026, bouton « Démarrer » :
	    capture arrêtée   -> CHECKABLE
	    capture en cours  -> CHECKABLE, CHECKED, UNAVAILABLE

	Renvoie None si la barre n'est plus exploitable ou si aucune commande
	cochable n'y figure — l'appelant retrouvera alors la barre. En l'absence de
	repère, rien ne sera annoncé plutôt qu'un état deviné.
	"""
	for child in _safeObject(lambda: toolBar.children) or []:
		states = _safeObject(lambda c=child: c.states) or set()
		if controlTypes.State.CHECKABLE in states:
			return controlTypes.State.CHECKED in states
	return None


# -- Fonctions de diagnostic ----------------------------------------------------


def _describe(obj, label):
	"""Retourne les lignes de description détaillée d'un objet NVDA.

	Le texte des objets porteurs de données de capture est masqué : rôle,
	états, position, identifiants et motifs UIA — tout ce qui sert réellement
	au diagnostic — restent en clair.
	"""
	lines = [f"--- {label} ---"]
	if obj is None:
		lines.append("objet : None")
		return lines
	redact = _holdsCaptureData(obj)
	lines.append(
		"resume : nom=%s role=%s etats=%s valeur=%s description=%s"
		% (
			REDACTED if redact else repr(_diag(lambda: obj.name)),
			_diag(lambda: obj.role),
			_diag(lambda: obj.states),
			REDACTED if redact else repr(_diag(lambda: obj.value)),
			REDACTED if redact else repr(_diag(lambda: obj.description)),
		)
	)
	lines.append(
		"fenetre : classe=%r controlID=%r handle=%r position=%r"
		% (
			_diag(lambda: obj.windowClassName),
			_diag(lambda: obj.windowControlID),
			_diag(lambda: obj.windowHandle),
			_diag(lambda: obj.location),
		)
	)
	lines.append("enfants : %s" % _diag(lambda: obj.childCount))
	lines.append(
		"displayText : %s"
		% (REDACTED if redact else repr(_diag(lambda: getattr(obj, "displayText", None))))
	)
	lines.append("devInfo :")
	for info in _safeObject(lambda: obj.devInfo) or []:
		text = str(info)
		if redact and text.lstrip().startswith(REDACTED_DEVINFO_PREFIXES):
			lines.append("  %s %s" % (text.lstrip().split(":", 1)[0] + ":", REDACTED))
			continue
		lines.append("  %s" % text)
	return lines


def _holdsCaptureData(obj):
	"""Indique si cet objet peut porter des données de la capture.

	Toute cellule d'arborescence de Wireshark en porte potentiellement — liste
	des paquets, détails du paquet, fenêtres de statistiques — à la seule
	exception de la liste des interfaces, qui ne contient que des noms de
	périphériques. Le texte de ces objets n'est jamais écrit dans le journal :
	un relevé de diagnostic doit renseigner sur la structure de l'interface,
	pas sur le trafic observé.
	"""
	role = _safeObject(lambda: obj.role)
	if role not in (controlTypes.Role.TREEVIEWITEM, controlTypes.Role.LISTITEM):
		return False
	return not _belongsToInterfaceTree(obj)


def _scanCommands(root):
	"""Relève les commandes de l'interface avec leur nom et leur état.

	Le parcours est en largeur, borné en profondeur et en nombre d'objets, et
	ne descend que dans des conteneurs. Il ne touche donc jamais au contenu de
	la capture. Objectif : comparer l'état des commandes entre capture arrêtée
	et capture en cours, l'état étant une propriété structurelle, indépendante
	de la langue de l'interface.
	"""
	lines = []
	queue = [(root, 0)]
	visited = 0
	while queue and visited < MAX_SCAN_OBJECTS:
		obj, depth = queue.pop(0)
		visited += 1
		role = _safeObject(lambda o=obj: o.role)
		if role in COMMAND_ROLES:
			lines.append(
				"  %s | nom=%r | description=%r | etats=%s | id=%r"
				% (
					role,
					_rawUIAName(obj),
					_diag(lambda o=obj: o.description),
					_diag(lambda o=obj: o.states),
					_uiaAutomationId(obj),
				)
			)
		if depth < MAX_SCAN_DEPTH and (depth == 0 or role in CONTAINER_ROLES):
			for child in _safeObject(lambda o=obj: o.children) or []:
				queue.append((child, depth + 1))
	return lines, visited


def _dumpObject(obj, title, withAncestors=True, withChildren=True, withSiblings=True):
	"""Écrit dans le journal NVDA un relevé complet autour d'un objet."""
	lines = [MARK_BEGIN.format(title=title)]
	lines.extend(_describe(obj, "OBJET COURANT"))

	if obj is not None and withAncestors:
		parent = _safeObject(lambda: obj.parent)
		level = 1
		while parent is not None and level <= MAX_ANCESTORS:
			lines.extend(_describe(parent, f"PARENT niveau {level}"))
			parent = _safeObject(lambda p=parent: p.parent)
			level += 1

	if obj is not None and withSiblings:
		lines.extend(_describe(_safeObject(lambda: obj.previous), "FRERE PRECEDENT"))
		lines.extend(_describe(_safeObject(lambda: obj.next), "FRERE SUIVANT"))

	if obj is not None and withChildren:
		children = _safeObject(lambda: obj.children) or []
		lines.append(f"--- ENFANTS ({len(children)}) ---")
		for index, child in enumerate(children[:MAX_CHILDREN]):
			lines.extend(_describe(child, f"ENFANT {index}"))
		if len(children) > MAX_CHILDREN:
			lines.append(f"... {len(children) - MAX_CHILDREN} enfant(s) non journalise(s)")

	lines.append(MARK_END.format(title=title))
	log.info("\n".join(str(line) for line in lines))


class AppModule(appModuleHandler.AppModule):
	"""App Module actif uniquement dans wireshark.exe."""

	#: Journalisation des événements d'accessibilité : désactivée par défaut.
	logEvents = False

	#: Barre d'outils principale, conservée entre deux lectures de l'état de la
	#: capture. Retrouvée automatiquement si elle cesse d'être exploitable.
	_mainToolBar = None

	#: Numéro de la surveillance de capture en cours. Chaque Ctrl+E l'incrémente,
	#: ce qui périme silencieusement la surveillance précédente : deux frappes
	#: rapprochées ne peuvent pas annoncer deux fois le même changement.
	_captureWatch = 0

	# -- Attribution des classes de correction ----------------------------------

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		"""Greffe la correction sur les objets de la liste des interfaces."""
		if not isinstance(obj, UIA):
			return
		role = _safeObject(lambda: obj.role)
		if role == controlTypes.Role.TREEVIEWITEM:
			if _belongsToInterfaceTree(obj):
				clsList.insert(0, InterfaceTreeCell)
			elif _belongsToPacketList(obj):
				clsList.insert(0, PacketListRow)
			else:
				# Toute autre arborescence de Wireshark : la correction ne
				# s'applique qu'aux vues à une seule colonne, ce que la classe
				# vérifie elle-même au moment de la lecture.
				clsList.insert(0, SingleColumnTreeCell)
		elif role == controlTypes.Role.TREEVIEW:
			if _belongsToInterfaceTree(obj):
				clsList.insert(0, InterfaceTreeList)
		elif role == controlTypes.Role.BUTTON:
			# Bouton sans nom : son infobulle, exposée en description et déjà
			# traduite par Wireshark, servira de nom.
			if not _rawUIAName(obj):
				clsList.insert(0, DescribedButton)
		elif role == controlTypes.Role.STATICTEXT:
			# Étiquette atteignable par Tabulation : c'est un lien, pas un
			# élément de mise en page.
			states = _safeObject(lambda: obj.states) or set()
			if controlTypes.State.FOCUSABLE in states:
				clsList.insert(0, FocusableLabel)

	# -- État de la capture -----------------------------------------------------

	@script(
		# Translators: description of the capture start/stop command.
		description=_("Start or stop the capture, and report the new state"),
		gesture="kb:control+e",
		category="Wireshark",
	)
	def script_toggleCapture(self, gesture):
		# L'état est lu AVANT de transmettre la touche. L'arrêt d'une capture
		# est instantané : lu après, l'état « avant » serait déjà l'état
		# « après », et aucun changement ne serait jamais détecté. De plus, si
		# Wireshark ouvre sa boîte « paquets non enregistrés », la fenêtre au
		# premier plan n'est plus la fenêtre principale et la barre d'outils
		# devient introuvable.
		before = self._captureState()
		# La touche est ensuite transmise à Wireshark : son comportement reste
		# strictement intact, y compris si la suite échoue.
		gesture.send()
		log.info("WIRESHARK-DIAG ctrl+E intercepté, état avant = %r" % before)
		if before is None:
			# État non exposé : ne rien annoncer plutôt que deviner.
			return
		self._captureWatch += 1
		self._watchCaptureState(self._captureWatch, before, CAPTURE_CHECK_ATTEMPTS)

	def _captureState(self):
		"""Lit l'état de la capture en réutilisant la barre d'outils trouvée.

		La recherche de la barre parcourt l'arbre d'accessibilité ; la refaire à
		chaque contrôle retarderait la frappe. L'objet est donc conservé, et
		retrouvé automatiquement s'il cesse d'être exploitable — changement de
		fenêtre, redémarrage de Wireshark.
		"""
		toolBar = self._mainToolBar
		if toolBar is not None:
			capturing = _readCaptureState(toolBar)
			if capturing is not None:
				return capturing
		foreground = _safeObject(api.getForegroundObject)
		if foreground is None:
			return None
		# La fenêtre au premier plan peut appartenir à une autre application :
		# l'utilisateur a pu changer de fenêtre juste après avoir lancé la
		# capture. Sans cette garde, le parcours irait explorer l'arbre
		# d'accessibilité de cette application, sur le fil principal de NVDA.
		if _safeObject(lambda: foreground.processID) != self.processID:
			return None
		toolBar = _findMainToolBar(foreground)
		self._mainToolBar = toolBar
		if toolBar is None:
			return None
		return _readCaptureState(toolBar)

	def _watchCaptureState(self, watch, before, attempts):
		"""Relit l'état de la capture après Ctrl+E, un nombre borné de fois.

		Deux relevés d'événements ont établi que Wireshark n'émet **aucun**
		événement d'accessibilité au démarrage ni à l'arrêt de la capture : ni
		changement de nom, ni changement d'état. Les seuls événements observés
		venaient de la barre de défilement de la liste, qui bouge aussi lorsque
		l'utilisateur fait simplement défiler les paquets : ce n'est pas un
		repère fiable.

		À défaut d'événement, l'état est relu à cadence fixe. Ce contrôle
		démarre sur une action de l'utilisateur, s'arrête dès que l'état a
		changé, et ne survit pas à son budget de sept secondes et demie : ce n'est pas
		une boucle de surveillance permanente, et rien ne tourne au repos.

		Le budget laisse à Wireshark le temps d'ouvrir sa boîte « paquets non
		enregistrés », d'attendre la réponse, puis de démarrer. Si l'utilisateur
		annule, l'état ne change pas et rien n'est annoncé.
		"""
		if watch != self._captureWatch:
			# Une frappe plus récente a pris la main.
			return
		if attempts <= 0:
			log.info("WIRESHARK-DIAG ctrl+E : aucun changement d'état observé")
			return
		current = self._captureState()
		if current is not None and current != before:
			log.info("WIRESHARK-DIAG ctrl+E : état après = %r" % current)
			self._announceCaptureState(current)
			return
		core.callLater(
			CAPTURE_CHECK_INTERVAL_MS, self._watchCaptureState, watch, before, attempts - 1
		)

	def _announceCaptureState(self, capturing):
		if capturing:
			# Translators: reported when a capture has started.
			ui.message(_("Capture started"))
		else:
			# Translators: reported when a capture has stopped.
			ui.message(_("Capture stopped"))

	@script(
		# Translators: description of the command reporting the capture state.
		description=_("Report whether a capture is running"),
		gesture="kb:NVDA+shift+c",
		category="Wireshark",
	)
	def script_reportCaptureState(self, gesture):
		capturing = self._captureState()
		if capturing is None:
			# Translators: reported when Wireshark does not expose the capture state.
			ui.message(_("Capture state unavailable"))
			return
		if capturing:
			# Translators: reported when a capture is currently running.
			ui.message(_("Capture running"))
		else:
			self._announceCaptureState(False)

	# -- Commandes de lecture ---------------------------------------------------

	@script(
		# Translators: description of the row reading command.
		description=_("Read the current row column by column"),
		gesture="kb:NVDA+shift+w",
		category="Wireshark",
	)
	def script_readCurrentRow(self, gesture):
		focus = api.getFocusObject()
		# Trace sans contenu : elle sert uniquement à vérifier que le raccourci
		# atteint bien l'extension, sans rien écrire des données du paquet.
		log.info("WIRESHARK-DIAG lecture de ligne demandée")
		# La commande vaut pour toute ligne de Wireshark répartie sur plusieurs
		# cellules — liste des paquets, liste des interfaces, fenêtres de
		# statistiques — et non pour la seule liste des paquets.
		if _safeObject(lambda: focus.role) not in ROW_ROLES:
			# Translators: reported when the command is used outside a list with columns.
			ui.message(_("This command works in a list with columns"))
			return
		# Le texte est prononcé, jamais journalisé : il contient des adresses et
		# des ports, que le projet s'interdit d'écrire dans le journal.
		description = _describeRow(focus)
		if description:
			ui.message(description)
		else:
			# Translators: reported when the row holds no readable data.
			ui.message(_("No readable data on this row"))

	# -- Commandes de diagnostic ------------------------------------------------

	@script(
		# Translators: description of a diagnostic command.
		description=_("Log the state of the Wireshark commands"),
		gesture="kb:NVDA+shift+e",
		category="Wireshark",
	)
	def script_dumpCaptureCommands(self, gesture):
		root = _safeObject(api.getForegroundObject)
		if root is None:
			# Translators: reported when the Wireshark window cannot be found.
			ui.message(_("Wireshark window not found"))
			return
		lines, visited = _scanCommands(root)
		log.info(
			"\n".join(
				[
					MARK_BEGIN.format(title="COMMANDES"),
					"titre de la fenetre : %r" % _diag(lambda: root.windowText),
					"objets parcourus : %d" % visited,
					*lines,
					MARK_END.format(title="COMMANDES"),
				]
			)
		)
		# Translators: confirms that the report has been written to the log.
		ui.message(_("Command report written to the log"))

	@script(
		# Translators: description of a diagnostic command.
		description=_("Log the accessibility information of the focused object"),
		category="Wireshark",
	)
	def script_dumpFocus(self, gesture):
		_dumpObject(api.getFocusObject(), "FOCUS")
		# Translators: confirms that the report has been written to the log.
		ui.message(_("Focus report written to the log"))

	@script(
		# Translators: description of a diagnostic command.
		description=_("Log the accessibility information of the navigator object"),
		category="Wireshark",
	)
	def script_dumpNavigator(self, gesture):
		_dumpObject(api.getNavigatorObject(), "OBJET NAVIGATEUR")
		# Translators: confirms that the report has been written to the log.
		ui.message(_("Navigator object report written to the log"))

	@script(
		# Translators: description of a diagnostic command.
		description=_("Toggle logging of accessibility events"),
		category="Wireshark",
	)
	def script_toggleEventLogging(self, gesture):
		self.logEvents = not self.logEvents
		if self.logEvents:
			# Translators: reported when event logging has been enabled.
			ui.message(_("Event logging enabled"))
		else:
			# Translators: reported when event logging has been disabled.
			ui.message(_("Event logging disabled"))

	# -- Journalisation des événements ------------------------------------------

	def _logEvent(self, eventName, obj):
		"""Trace un événement de façon compacte : une ligne par événement."""
		if not self.logEvents:
			return
		log.info(
			"WIRESHARK-DIAG evenement %s : nom=%s role=%s etats=%s classe=%r"
			% (
				eventName,
				REDACTED if _holdsCaptureData(obj) else repr(_diag(lambda: obj.name)),
				_diag(lambda: obj.role),
				_diag(lambda: obj.states),
				_diag(lambda: obj.windowClassName),
			)
		)

	def event_gainFocus(self, obj, nextHandler):
		self._logEvent("gainFocus", obj)
		if isinstance(obj, FocusableLabel):
			# Trace systématique, indépendante de la journalisation des
			# événements : elle sert à vérifier que NVDA reçoit bien le focus
			# sur ces étiquettes. Ne contient que le nom du lien.
			log.info("WIRESHARK-DIAG lien focalise : nom=%r" % _diag(lambda: obj.name))
			nextHandler()
			# Corriger le rôle n'a pas suffi : NVDA reste muet sur ces
			# étiquettes Qt. On les annonce donc explicitement, après le
			# traitement normal, afin que le suivi du focus, le braille et le
			# curseur de revue restent intacts.
			self._announce(obj)
			return
		nextHandler()

	def _announce(self, obj):
		"""Annonce un objet comme NVDA le ferait lors d'une prise de focus."""
		try:
			speech.speakObject(obj, reason=controlTypes.OutputReason.FOCUS)
		except Exception:  # noqa: BLE001
			# Repli si la constante de raison change de place selon la version.
			try:
				speech.speakObject(obj)
			except Exception:  # noqa: BLE001
				name = _safeObject(lambda: obj.name) or ""
				if name:
					ui.message(name)

	def event_focusEntered(self, obj, nextHandler):
		self._logEvent("focusEntered", obj)
		nextHandler()

	def event_selection(self, obj, nextHandler):
		self._logEvent("selection", obj)
		nextHandler()

	def event_selectionAdd(self, obj, nextHandler):
		self._logEvent("selectionAdd", obj)
		nextHandler()

	def event_selectionRemove(self, obj, nextHandler):
		self._logEvent("selectionRemove", obj)
		nextHandler()

	def event_selectionWithIn(self, obj, nextHandler):
		self._logEvent("selectionWithIn", obj)
		nextHandler()

	def event_nameChange(self, obj, nextHandler):
		self._logEvent("nameChange", obj)
		nextHandler()

	def event_valueChange(self, obj, nextHandler):
		self._logEvent("valueChange", obj)
		nextHandler()

	def event_stateChange(self, obj, nextHandler):
		self._logEvent("stateChange", obj)
		nextHandler()
