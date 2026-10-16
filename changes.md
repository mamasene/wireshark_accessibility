# Journal des modifications

## 1.0.0 — première version publiable

### Internationalisation, corrigée à la racine

- Le module n'appelait pas `addonHandler.initTranslation()`. Sans cet appel,
  `_()` consulte le catalogue de traduction de NVDA et non celui de
  l'extension : **aucune traduction livrée avec l'extension n'aurait jamais
  été utilisée**. Le défaut passait inaperçu parce que les chaînes source
  étaient en français et l'utilisateur francophone. Exigence du guide des
  développeurs de NVDA, section « Plugin Translation ».
- Les chaînes source passent donc à l'anglais, langue de base déclarée dans
  `buildVars.py`, et le français est fourni comme traduction dans
  `addon/locale/fr`. Un utilisateur francophone entend le français, un
  anglophone l'anglais, et un traducteur dispose d'un catalogue utilisable.
  Les vingt-trois chaînes sont traduites et le catalogue compile sans
  avertissement.
- Les commentaires destinés aux traducteurs étaient eux-mêmes en français.
  Passés à l'anglais : c'est la langue de travail des traducteurs de NVDA.
- Le résumé, la description et le journal des modifications affichés par le
  magasin d'extensions sont désormais en anglais, avec leur traduction
  française livrée dans le manifeste traduit.

### Documentation

- `addon/doc/fr/readme.md` était une **copie figée de la phase 1**, annonçant
  qu'aucune annonce de NVDA n'était modifiée. Elle partait dans le paquet avec
  cette information fausse. Réécrite.
- Documentation utilisateur complète, en anglais et en français : ce qui est
  corrigé et pourquoi, les commandes, le traitement des données de capture,
  et ce qui ne sera pas corrigé — le graphique d'activité, dont Wireshark
  n'expose aucune valeur.
- La liste des défauts à remonter en amont vers Wireshark est publiée dans la
  documentation plutôt que gardée dans les notes internes.

### Paquet

- Le motif d'exclusion du bytecode ne pouvait pas fonctionner : les motifs sont
  comparés au chemin **tel qu'il apparaît dans l'archive**, donc relativement à
  `addon/`, et le motif commençait par `addon/`. Corrigé, et les catalogues
  source `.po` sont également exclus — NVDA ne lit que les `.mo` compilés.

### Reste à faire avant soumission au magasin

- `addon_url` et `addon_sourceURL` sont encore vides. Le champ `sourceURL` est
  **obligatoire** dans la soumission, et la page d'accueil déclarée doit
  correspondre au champ `url` du manifeste. Les deux doivent commencer par
  `https://`. Ils ne pourront être renseignés qu'une fois le dépôt public créé.

## 0.9.0 — revue de code avant publication

### Vie privée

- **Aucune donnée de capture n'est plus écrite dans le journal.** Les relevés
  journalisaient le nom des objets : depuis que les lignes de paquets portent un
  nom recomposé, cela revenait à écrire ports, drapeaux TCP et descriptions de
  paquets ; le relevé d'un objet ayant le focus dans la liste journalisait en
  outre les cellules voisines, donc les adresses source et destination.
  Le texte des cellules d'arborescence — paquets, détails, statistiques — est
  désormais remplacé par un marqueur. Rôles, états, positions, identifiants et
  motifs UIA restent en clair : c'est ce qui sert au diagnostic. La liste des
  interfaces fait exception, elle ne contient que des noms de périphériques.
- Les trois commandes de diagnostic **n'ont plus de raccourci par défaut**.
  Elles restent assignables dans NVDA, Préférences, Gestes de commandes,
  catégorie « Wireshark ». Un relevé d'accessibilité n'a pas à pouvoir être
  déclenché par inadvertance pendant une formation.

### Correction

- La surveillance qui suit `Ctrl+E` pouvait **parcourir l'interface d'une autre
  application**. Si l'utilisateur changeait de fenêtre juste après la frappe et
  que la barre d'outils en cache devenait illisible, le module explorait jusqu'à
  quatre cents objets de la fenêtre au premier plan, trente fois de suite, sur
  le fil principal de NVDA. Le processus de la fenêtre est désormais vérifié.
- Deux `Ctrl+E` rapprochés lançaient deux surveillances, qui annonçaient deux
  fois le même changement. Chaque frappe périme silencieusement la précédente.
- `NVDA+majuscule+W` **refusait la liste des interfaces**, alors que la version
  précédente annonçait le contraire : le garde exigeait le rôle « élément
  d'arborescence », que ce module remplace justement par « élément de liste »
  sur ces cellules.
- La fonction de lecture tolérante aux erreurs renvoyait un texte d'erreur au
  lieu de la valeur de repli demandée. Conséquences : un relevé d'objet illisible
  journalisait une quarantaine de lignes d'un seul caractère, et une annonce de
  repli aurait pu prononcer le message d'exception. Les deux usages passent
  désormais par une fonction qui renvoie franchement None.

### Code mort et doublons

- `_isCapturing` n'était plus appelée depuis la mise en cache de la barre
  d'outils. Supprimée ; la preuve relevée qu'elle documentait rejoint la
  fonction réellement utilisée.
- Le parcours géométrique d'une ligne était écrit **trois fois**, et les trois
  copies avaient déjà divergé. Il n'en reste qu'une.
- L'en-tête du module annonçait « aucune interception clavier » et « aucune
  temporisation, aucune boucle de surveillance » : faux depuis la 0.8.0. Il
  décrit désormais ce que le code fait, et pourquoi la seule temporisation du
  module est justifiée.

### Tests

- Ajout de `tests/test_wireshark.py`, qui remplace les modules de NVDA par des
  doublures et exerce la logique qui n'en dépend pas : découpage des lignes en
  cellules, appariement des en-têtes, lecture de l'état de la capture, masquage
  des données. Vingt contrôles, sur des objets factices reproduisant la
  géométrie et les états réellement relevés dans Wireshark 4.6.8.

## 0.8.1 — correction de l'annonce sur Ctrl+E

- L'annonce du démarrage et de l'arrêt de la capture ne se produisait
  pratiquement jamais. L'état de départ était lu **après** que la touche eut
  été transmise à Wireshark : l'arrêt d'une capture étant instantané, l'état
  « avant » était déjà l'état « après », et aucun changement ne pouvait être
  détecté. Au démarrage, la boîte « paquets non enregistrés » passait au
  premier plan, la barre d'outils devenait introuvable et la commande
  abandonnait. L'état est désormais lu avant la transmission de la touche.
- La barre d'outils principale est conservée d'une lecture à l'autre, afin que
  la lecture préalable ne retarde pas la frappe. Elle est retrouvée
  automatiquement si elle cesse d'être exploitable.
- Le budget de contrôle passe de quatre à sept secondes et demie : la boîte
  « paquets non enregistrés » attend une réponse de l'utilisateur avant que la
  capture ne démarre.
- Trois lignes de journal encadrent désormais l'interception de `Ctrl+E` —
  état avant, état après, ou absence de changement. Elles ne contiennent aucune
  donnée de paquet.

## 0.8.0 — démarrage et arrêt de la capture

- `Ctrl+E` annonce désormais « Démarrage de la capture » ou « Capture
  arrêtée ». La touche est d'abord transmise à Wireshark : son comportement
  reste strictement intact.
- **Pourquoi une relecture d'état plutôt qu'un événement.** Deux relevés
  d'événements ont établi que Wireshark n'émet aucun événement d'accessibilité
  au démarrage ni à l'arrêt de la capture : ni changement de nom, ni changement
  d'état. Les seuls événements observés venaient de la barre de défilement de
  la liste des paquets, qui bouge aussi lorsqu'on fait simplement défiler les
  paquets — ce n'est pas un repère fiable.
  À défaut d'événement, l'état est relu à cadence fixe après la frappe. Le
  contrôle démarre sur une action de l'utilisateur, s'arrête dès que l'état a
  changé, et ne survit pas à un budget de quatre secondes. Rien ne tourne au
  repos : ce n'est pas une boucle de surveillance permanente.
- **Le repère retenu est un état, pas un libellé.** Dans la barre d'outils
  principale — identifiée par son identifiant d'automatisation, issu du code
  C++ de Wireshark — la première commande cochable est l'action de capture.
  Relevé du 20 septembre 2026 : `CHECKABLE` seule capture arrêtée,
  `CHECKABLE, CHECKED, UNAVAILABLE` capture en cours. Ce critère ne dépend pas
  de la langue de l'interface.
  Le titre de la fenêtre distingue lui aussi les deux états — « *Wi-Fi » contre
  « Capturing from Wi-Fi » — mais c'est un libellé, donc traduisible : il a été
  écarté.
- Si l'état n'est pas exposé, ou si l'utilisateur annule la boîte de dialogue
  « paquets non enregistrés », **rien n'est annoncé** : aucun état n'est deviné.
- Nouvelle commande `NVDA+majuscule+C` : annonce à tout moment si une capture
  est en cours. Utile lorsque la capture a été lancée depuis la barre d'outils
  ou le menu plutôt que par `Ctrl+E`.

## 0.7.2 — liste des paquets

- La commande de lecture de ligne passe sur `NVDA+majuscule+W` : la combinaison
  précédente n'atteignait pas l'extension, vraisemblablement retenue par une
  autre extension installée. Elle écrit désormais une ligne dans le journal à
  chaque appel — sans aucun contenu de paquet — afin de distinguer un conflit
  de raccourci d'une erreur dans la commande.
- Nouvelle commande de diagnostic `NVDA+majuscule+E` : relève l'état de toutes
  les commandes de l'interface — barres d'outils, boutons, entrées de menu —
  ainsi que le titre de la fenêtre. Le relevé, effectué capture arrêtée puis
  capture en cours, doit fournir le repère manquant pour annoncer le démarrage
  et l'arrêt de la capture. Le parcours est borné en profondeur et en nombre
  d'objets, et ne descend pas dans les arborescences, qui portent les données
  de la capture.
- Deux relevés d'événements ont établi que **Wireshark n'émet aucun événement
  d'accessibilité au démarrage ni à l'arrêt de la capture** : ni changement de
  nom, ni changement d'état. Les seuls événements observés proviennent de la
  barre de défilement de la liste des paquets, ce qui ne constitue pas un
  repère fiable — la barre bouge aussi lorsqu'on fait défiler la liste.

## 0.7.1 — liste des paquets

- Les lignes de la liste des paquets étaient annoncées par leur seul numéro :
  Wireshark répartit chaque paquet sur sept colonnes et pose le focus sur la
  première, qui ne contient que ce numéro. L'annonce reprend désormais la
  dernière colonne renseignée de la ligne — la colonne « Info » dans la
  disposition par défaut — ainsi que la position sous la forme « 3 sur 18 ».
- Le numéro est annoncé comme « trame 3 » plutôt que « 3 », afin que l'annonce
  commence par un mot et non par un chiffre nu.
- L'horodatage, la source et la destination sont volontairement écartés de
  l'annonce automatique : ce sont des suites de chiffres qu'une synthèse vocale
  énonce caractère par caractère, coûteuses à l'oreille lorsqu'on parcourt la
  liste. Elles restent accessibles par la nouvelle commande de lecture.
- Nouvelle commande `NVDA+shift+W` : lit la ligne courante colonne par
  colonne, chaque valeur précédée du libellé de sa colonne. Les libellés sont
  lus dans l'interface, donc traduits, et jamais présumés. La commande vaut pour
  toute liste en colonnes de Wireshark, et non pour la seule liste des paquets.
- L'état « réduit » est conservé : il signale que la ligne porte une
  arborescence de détails, atteignable par Tabulation.
- Les propriétés de tableau de la liste des paquets restent intactes, afin que
  la navigation par tableau de NVDA continue de fonctionner.
- Les arborescences à une seule colonne, dont celle des détails du paquet,
  n'annoncent plus « ligne 1, colonne 1 » : Qt expose chaque ligne comme une
  cellule de tableau même lorsqu'il n'y a qu'une colonne. Le niveau de
  profondeur, lui, est conservé : il distingue un protocole de ses champs.

## 0.6.0 — annonce explicite des liens

- Présenter les liens de la section « Learn » comme des liens n'a pas suffi :
  NVDA reçoit bien ces objets, avec leur nom et le rôle corrigé, mais reste
  muet. Ils sont désormais annoncés explicitement après le traitement normal
  du focus, qui reste intact pour le braille et le curseur de revue.
- Une ligne de journal est écrite à chaque prise de focus sur ces liens, afin
  de vérifier que NVDA reçoit bien l'événement.

## 0.5.0 — liens de la section « Learn »

- Les quatre liens de la section « Learn » de la page d'accueil — documentation,
  wiki, questions et réponses, listes de diffusion — étaient traversés par la
  Tabulation sans que NVDA n'annonce quoi que ce soit. Wireshark les expose
  comme du texte statique, que NVDA traite comme de la mise en page.
  Ils sont désormais présentés comme des liens et annoncés normalement.
- La règle vaut pour toute étiquette de Wireshark atteignable au clavier.

## 0.4.0 — boutons sans nom

- Les boutons qui n'exposent aucun nom accessible, mais dont l'infobulle est
  exposée en description, sont désormais annoncés avec cette infobulle. Premier
  cas rencontré : le bouton signets du filtre de capture, jusqu'ici annoncé
  « bouton » et rien d'autre.
- La description n'est pas répétée après le nom qu'elle vient de fournir.

## 0.3.0 — finition des annonces

- La position dans la liste est annoncée sous la forme « 3 sur 15 » au lieu de
  « ligne 3, niveau 1 » : le niveau de profondeur, toujours égal à 1, est
  supprimé, et le nombre total d'interfaces est désormais indiqué.
- Les lignes ne se déclarent plus comme des cellules de tableau, Qt les
  exposant simultanément en arborescence et en tableau.

## 0.2.0 — premier prototype correctif

- La **liste des interfaces de capture** de la page d'accueil est corrigée :
  - le nom de l'interface est annoncé lors du déplacement avec les flèches,
    alors que Wireshark le plaçait dans une cellule voisine que NVDA
    n'atteignait pas ;
  - la liste et ses lignes sont annoncées comme une liste et un élément de
    liste, au lieu d'une arborescence ;
  - la liste reprend le nom traduit de son cadre (« Liste des interfaces »).
- Aucune activité réseau n'est annoncée : Wireshark n'expose aucune valeur
  pour le graphique d'activité.
- Aucun raccourci de Wireshark n'est intercepté.
- Les trois commandes de diagnostic de la version 0.1.0 sont conservées.

## 0.1.0 — version de diagnostic

- Création du projet à partir du modèle communautaire AddonTemplate.
- App Module de **diagnostic** pour `wireshark.exe` :
  - `NVDA+control+shift+D` : relevé complet de l'objet ayant le focus,
    de ses parents, de ses frères et de ses enfants dans le journal NVDA ;
  - `NVDA+control+shift+N` : même relevé pour l'objet navigateur ;
  - `NVDA+control+shift+L` : active ou désactive la journalisation des
    événements d'accessibilité (désactivée par défaut).
- Aucune modification des annonces de NVDA à ce stade.
