# Résultats du diagnostic — liste des interfaces de capture

Relevés effectués le 19 septembre 2026.

## Environnement mesuré

| Élément | Valeur relevée |
|---|---|
| NVDA | 2026.2, Python 3.13.13, comtypes 1.4.13 |
| Windows | Windows 11 25H2 (10.0.26200.9457) |
| Wireshark | 4.6.8 (`appModule.productVersion`) |
| Pont d'accessibilité | **UI Automation**, `UIA frameworkID: Qt`, fournisseur `qwindows.dll` |
| Classe de fenêtre | `Qt6103QWindowIcon` — fenêtre unique pour toute l'interface |

Aucun IAccessible2 ni MSAA natif : tout passe par UIA, avec seulement
`LegacyIAccessiblePattern` en repli.

## Structure réellement exposée

```
WiresharkMainWindow (WINDOW)
└── centralWidget (QWidget)
    └── mainStack (QStackedWidget)
        └── welcomePage (WelcomePage)
            ├── mainContentContainer (QWidget)
            │   ├── captureFilterComboBox (CaptureFilterCombo)
            │   └── interfaceFrame (InterfaceFrame)  ← nom : « Liste des interfaces »
            │       └── interfaceTree (QTreeView)    ← nom : '' (vide)
            │           └── 36 cellules = 12 lignes × 3 colonnes
            └── sidebarContainer
```

### Les trois colonnes d'une ligne

Mesuré sur la ligne « Wi-Fi » (toutes les lignes suivent le même schéma) :

| Colonne | Position | `name` | Patterns UIA |
|---|---|---|---|
| 0 | x=94, largeur **42** | **vide** | GridItem, TableItem, SelectionItem, Invoke, Value |
| 1 | x=136, largeur **411** | **« Wi-Fi »** | idem |
| 2 | x=547, largeur **783** | **vide** | idem |

La colonne 0 correspond à la colonne étroite de gauche (extcap / réglages),
la colonne 1 au nom d'affichage, la colonne 2 au graphique d'activité
(`IFTREE_COL_STATS`, peint par un delegate, donc sans texte).

### Cause exacte du silence de NVDA

Le focus se pose **systématiquement sur la cellule de la colonne 0**, dont le
`name` est vide. Exemple reproduit sur les 12 lignes :

```
OBJET COURANT : nom='' role=TREEVIEWITEM position=(94, 756, 42, 24)
FRERE SUIVANT : nom='Wi-Fi'                 position=(136, 756, 411, 24)
```

Les lignes ne sont donc **pas vides** : le nom existe, dans la cellule voisine,
sur la même ligne visuelle (même coordonnée `top`).

### Ordre des objets enfants

Les cellules sont listées ligne par ligne, colonne par colonne. Le nom de
l'interface est donc toujours accessible par `obj.next` depuis la cellule
focalisée, et identifiable sans ambiguïté par l'égalité de `location.top`.

Séquence relevée : Wi-Fi, VMware VMnet8, Adapter for loopback traffic capture,
Connexion au réseau local* 10, 9, 8, Connexion réseau Bluetooth, VMware VMnet1,
Connexion au réseau local* 2, 1, OpenVPN Data Channel Offload,
OpenVPN TAP-Windows6, puis, après rafraîchissement, USBPcap1, USBPcap2,
« Event Tracing for Windows (ETW) reader: etwdump ».

Le nombre d'enfants varie (36 puis 33) : **la liste est reconstruite à chaud**
quand Wireshark termine l'énumération des extcap.

### États

La cellule focalisée porte `FOCUSABLE, SELECTABLE, FOCUSED, SELECTED`.
La cellule porteuse du nom porte `FOCUSABLE, SELECTABLE, SELECTED`.
L'état sélectionné est donc correctement exposé sur toute la ligne.

### Graphique d'activité

`name=''`, `value=''`, `description=''`, `displayText=''`.
**Aucune valeur numérique n'est exposée.** Conformément à la consigne du projet,
l'extension n'annoncera rien à ce sujet.

## Classement des constats

| Catégorie | Constat |
|---|---|
| Déjà exposé correctement | Nom et description de `InterfaceFrame` (« Liste des interfaces »), de la page d'accueil, des boutons Discord / Donate ; états de sélection ; hiérarchie complète |
| Présent visuellement, absent de l'arbre | Valeur chiffrée du sparkline (`IFTREE_COL_STATS`) |
| Présent dans un objet voisin, non annoncé | **Nom de l'interface** — cause principale du problème |
| Accessible uniquement par le modèle d'affichage | Rien : `displayText` est vide partout, la revue écran ne servirait à rien ici |
| Nécessiterait Tshark / les données de Wireshark | Débit ou nombre de paquets par interface |
| Corrigeable par l'App Module | Annonce du nom de la ligne, rôle plus pertinent |
| À corriger en amont dans Wireshark | `name` vide sur `interfaceTree` ; cellules extcap et stats sans `Qt::AccessibleTextRole` ; `automationID` identique pour les boutons Discord et Donate ; bouton signets du filtre de capture sans nom |

## Conséquence pour l'architecture

Le nom étant présent dans l'arbre d'accessibilité et repérable par une
propriété structurelle (même `top`, cellule suivante), la correction relève
entièrement de l'App Module. Elle peut se faire par une **classe overlay** qui
recalcule `name`, sans gestionnaire d'événement, sans temporisation et sans
boucle de surveillance.

## Constats complémentaires — page d'accueil hors liste

Relevés du 19 septembre 2026, section « Learn » de la barre latérale.

### Liens muets

Quatre objets traversés par la Tabulation sans aucune annonce :
« User Documentation », « Wiki », « Questions and Answers », « Mailing Lists ».

| Propriété | Valeur |
|---|---|
| `role` | STATICTEXT |
| `name` | renseigné (« User Documentation », …) |
| `description` | renseignée (« Read the Wireshark user documentation online. », …) |
| `states` | FOCUSABLE, FOCUSED |
| `UIA className` | QLabel |
| `automationID` | `…learnSectionCard.learnLinkContainer.learnLink` |
| patterns | LegacyIAccessible, **Invoke** |

Le contenu est donc bien présent. Ces étiquettes entrent dans l'ordre de
tabulation et s'activent, mais leur rôle de texte statique conduit NVDA à les
traiter comme de la mise en page plutôt que comme du contenu.

Corrigé par l'App Module : toute étiquette focalisable est présentée comme un
lien et déclarée comme contenu.

### À remonter en amont

- Ces quatre libellés et leurs descriptions ne sont **pas traduits**, alors que
  le reste de la page d'accueil l'est.
- L'`automationID` `learnLink` est identique pour les quatre liens, comme
  l'était déjà `learnButton` pour Discord et Donate.

## Liste des paquets — premiers relevés

Relevés du 20 septembre 2026, capture en cours sur Wi-Fi.

### Structure

```
WiresharkMainWindow (titre « *Wi-Fi » pendant la capture)
└── centralWidget → mainStack → splitterMaster (QSplitter, 3 enfants)
    └── PacketList (QTreeView)  ← nom, valeur ET description : « Packet list »
        └── 133 enfants = 7 en-têtes + 18 lignes × 7 cellules
```

`UIA automationID` de la vue : `Packet list`.
`UIA automationID` des cellules : `…splitterMaster.PacketList`.

### Même cause que la liste des interfaces

Le focus se pose sur la **cellule de la colonne 0**, qui contient le numéro du
paquet. NVDA annonce donc « 1 », « 2 », « 3 » et rien d'autre.

Exemple, ligne 1 (`top=190`) :

| Colonne | Position | `name` |
|---|---|---|
| 0 — Numéro | x=-63, largeur 106 | `'1'` |
| 1 — Temps | x=43, largeur 150 | `'0.000000000'` |
| … | | |
| 6 — Info | x=793, largeur 1060 | `'62882 → 443 [ACK] Seq=1 Ack=1 Win=253 Len=1'` |

La colonne 0 est à **x négatif** : la vue est défilée horizontalement, le numéro
est partiellement hors écran. Le repère de ligne reste `location.top`.

### Ce qui est disponible et non annoncé

Toutes les colonnes portent un `name` renseigné. Les **en-têtes de colonne sont
exposés** comme objets de rôle HEADER — relevé : « Info », x=858, top=157.
Il est donc possible de nommer chaque valeur par sa colonne.

### Bruit supplémentaire

Chaque cellule porte l'état `COLLAPSED`, héritée de la sémantique arborescente
de Qt. NVDA annoncera « réduit » sur chaque paquet si rien n'est fait.

### En-têtes de colonne — relevé

Un en-tête a été capturé en entier : colonne « Info », `role: HEADER`,
`states: SELECTABLE`, `isFocusable: False`, position x=858, top=157.

Les cellules de données portent `FOCUSABLE, SELECTABLE`. Un en-tête se
distingue donc d'une cellule par son rôle, relevé et non présumé. Les en-têtes
sont les premiers enfants de la vue, dans l'ordre des colonnes.

### Contenu réel des lignes

Relevés du 20 septembre 2026, lignes 2 et 3 d'une capture Wi-Fi :

| Ligne | Colonne 0 (focus) | Colonne 1 | Dernière colonne |
|---|---|---|---|
| 2 | `2` | `0.006190900` | `443 → 58388 [ACK] Seq=1 Ack=2 Win=15 Len=0 SLE=1 SRE=2` |
| 3 | `3` | `1.014331500` | `[TCP Keep-Alive] 58388 → 443 [ACK] Seq=1 Ack=1 Win=251 Len=1` |

L'horodatage est une décimale à neuf chiffres : énoncé caractère par caractère
par une synthèse vocale, il sature l'annonce pour une information rarement
utile en parcourant la liste. La dernière colonne est longue — quarante à
soixante caractères — mais porte tout le sens : ports, drapeaux TCP, numéros de
séquence. La parole étant interrompue dès la flèche suivante, sa longueur ne
coûte rien lorsqu'on défile vite.

**Décision** : annonce automatique limitée au numéro de trame, à la dernière
colonne renseignée et à la position ; toutes les colonnes restant accessibles
par une commande dédiée.

### Les sept colonnes, relevées

La commande de lecture détaillée a confirmé la disposition complète :

```
No. 1, Time 0.000000000, Source 198.51.100.138, Destination 203.0.113.51,
Protocol TLSv1.2, Length 104, Info Application Data
```

Soit `No.`, `Time`, `Source`, `Destination`, `Protocol`, `Length`, `Info` —
la disposition par défaut de Wireshark, la colonne `Info` étant bien la
dernière.

**Les libellés d'en-tête ne sont pas traduits** alors que le reste de
l'interface l'est, comme les liens de la section « Learn » de la page
d'accueil. À remonter en amont.

### Navigation par tableau

Les propriétés de tableau sont laissées intactes sur la liste des paquets, qui
est un véritable tableau à sept colonnes. La navigation par tableau de NVDA
(contrôle+alt+flèches) doit donc rester disponible. **À confirmer par le test.**

## Arborescence des détails du paquet — premiers relevés

Relevé oral du 20 septembre 2026 : après Tabulation depuis une ligne de la
liste des paquets, NVDA annonce par exemple

```
Frame 3: Packet, 55 bytes on wire (440 bits), 55 bytes captured (440 bits)
on interface \Device\NPF_{XXXXXXXX-…}, id 0   réduit   ligne 1   1
colonne 1   niveau 1
```

Le texte est celui de Wireshark et n'est pas modifié. En revanche « ligne 1,
1, colonne 1 » est du bruit : Qt expose chaque ligne de QTreeView comme une
cellule de tableau, même lorsque l'arborescence n'a qu'une seule colonne.

Correction retenue : neutraliser les propriétés de tableau lorsque la vue
parente déclare **au plus une colonne**. Le critère est mesuré sur la vue, non
déduit de son nom : la correction vaut pour toute arborescence à une colonne
sans rien présumer de l'interface.

Le **niveau de profondeur est conservé** : dans cette arborescence, il
distingue un protocole de ses champs, il porte donc une information réelle.

## Démarrage et arrêt de la capture — relevé décisif

Relevés du 20 septembre 2026, trois appels consécutifs de `NVDA+majuscule+E` :
capture arrêtée, capture en cours, capture arrêtée de nouveau.

### Aucun événement d'accessibilité

Deux relevés d'événements distincts, dont un test dédié à `Ctrl+E`, n'ont
produit **ni `nameChange`, ni `stateChange`** au démarrage ou à l'arrêt de la
capture. Les seuls événements observés sont des `valueChange` de rôle
`SCROLLBAR` — valeur du rôle vérifiée contre l'énumération de NVDA 2026.2
installée sur le poste — c'est-à-dire la barre de défilement de la liste des
paquets. Elle bouge aussi lorsque l'utilisateur fait simplement défiler les
paquets : ce n'est pas un repère d'activité de capture.

### Deux repères exploitables

| Repère | Capture arrêtée | Capture en cours |
|---|---|---|
| Titre de la fenêtre | `*Wi-Fi` | `Capturing from Wi-Fi` |
| Bouton « Démarrer » | `CHECKABLE` | `CHECKABLE, CHECKED, UNAVAILABLE` |
| Bouton « Arrêter » | `UNAVAILABLE` | *(actif)* |
| Boutons Ouvrir, Sauvegarder, Fermer, Recharger, Options | *(actifs)* | `UNAVAILABLE` |

Le titre distingue bien les deux états, mais c'est un **libellé**, donc
traduisible : écarté.

Le **repère retenu est l'état coché de la première commande cochable de la
barre d'outils principale**. C'est une propriété structurelle, indépendante de
la langue. La barre est identifiée par son identifiant d'automatisation
`MainApplication.WiresharkMainWindow.mainToolBar`, issu du code C++ de
Wireshark ; la barre de filtrage porte l'identifiant distinct
`displayFilterToolBar`.

### Limite relevée

Tous les boutons de la barre d'outils partagent le même identifiant
d'automatisation, `…mainToolBar.QToolButton` : aucun ne peut être désigné
individuellement autrement que par sa position ou son état. À remonter en
amont dans Wireshark.

Noter aussi que les boutons de capture sont exposés avec deux rôles
différents : « Démarrer » est une case à cocher, « Arrêter » et « Redémarrer »
sont des boutons.
