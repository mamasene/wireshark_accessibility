# -*- coding: UTF-8 -*-
# Variables de compilation de l'extension.
# Structure alignée sur le modèle communautaire AddonTemplate.
#
# La langue de base est l'anglais : c'est elle que le magasin d'extensions de
# NVDA affiche, et celle à partir de laquelle les traducteurs travaillent. Le
# français est fourni comme traduction, dans addon/locale/fr.

from site_scons.site_tools.NVDATool.typings import AddonInfo, BrailleTables, SymbolDictionaries
from site_scons.site_tools.NVDATool.utils import _

addon_info = AddonInfo(
	# Nom interne de l'extension, utilisé par NVDA et comme identifiant dans le
	# magasin. Lettres, chiffres, soulignés et tirets uniquement.
	addon_name="wiresharkAccessibility",
	# Translators: user visible name of the add-on.
	addon_summary=_("Wireshark Accessibility"),
	# Translators: long description of the add-on.
	addon_description=_("""Makes the Wireshark graphical interface usable with a screen reader.
Wireshark splits every row of its interface and packet lists into one cell per
column, and puts focus on a cell holding no useful text: rows are now announced
with their real content and their position in the list. Buttons with no
accessible name are announced using their tooltip, and the links of the welcome
page, previously silent, are announced. Ctrl+E reports the start and the stop of
a capture, which Wireshark signals by no accessibility event at all.
Capture data is never written to the NVDA log."""),
	addon_version="1.0.0",
	# Translators: what's new in this version.
	addon_changelog=_("""First release.
The capture interface list and the packet list are announced with their
content and their position. Buttons without an accessible name use their
tooltip. The links on the welcome page are announced. Ctrl+E reports the start
and the stop of a capture. Meaningless row and column numbers are no longer
announced in single column trees, such as the packet detail tree.
Diagnostic recordings redact capture data, and the diagnostic commands have no
shortcut assigned by default."""),
	addon_author="Mama Sene <tech.access33@gmail.com>",
	# À renseigner avant soumission au magasin : le champ sourceURL de la
	# soumission est obligatoire, et la page d'accueil doit correspondre à ce
	# champ url. Les deux doivent commencer par https://.
	addon_url=None,
	addon_sourceURL=None,
	addon_docFileName="readme.html",
	# Versions d'API de NVDA. minimumNVDAVersion doit rester inférieure ou égale
	# à lastTestedNVDAVersion, et toutes deux doivent exister dans la liste des
	# versions d'API du magasin.
	addon_minimumNVDAVersion="2024.1",
	addon_lastTestedNVDAVersion="2026.1",
	addon_updateChannel=None,
	addon_license="GPL v2",
	addon_licenseURL="https://www.gnu.org/licenses/old-licenses/gpl-2.0.html",
)

# Fichiers Python contenant des chaînes traduisibles.
pythonSources: list[str] = ["addon/appModules/*.py"]

# Fichiers fournissant les chaînes à traduire.
i18nSources: list[str] = pythonSources + ["buildVars.py"]

# Fichiers exclus du paquet final. Les motifs sont comparés au chemin tel qu'il
# apparaîtra DANS l'archive, donc relativement à addon/ — un motif préfixé par
# « addon/ » ne correspondrait jamais à rien.
#   - le bytecode éventuellement déposé par le banc d'essai : il serait compilé
#     pour la version de Python du poste de travail, non pour celle de NVDA ;
#   - les catalogues source .po : NVDA ne lit que les .mo compilés.
excludedFiles: list[str] = ["*.pyc", "locale/*/LC_MESSAGES/*.po"]

# Langue de base du code source et de la documentation.
baseLanguage: str = "en"

# Extensions Markdown nécessaires à la documentation (tableaux).
markdownExtensions: list[str] = ["markdown.extensions.tables"]

# Aucune table braille ni dictionnaire de symboles personnalisés.
brailleTables: BrailleTables = {}
symbolDictionaries: SymbolDictionaries = {}
