# Accessibilité de Wireshark

Extension NVDA qui rend l'interface graphique de Wireshark utilisable au
lecteur d'écran, sous Windows.

* Auteurs : Mama Sene, Emmanuel
* Licence : [GNU General Public License version 2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
* Nécessite NVDA 2024.1 ou ultérieur ; dernière version testée : NVDA 2026.1
* Développée avec Wireshark 4.6.8 sous Windows 11

## Pourquoi cette extension

Les techniciens réseau non-voyants se replient en général sur **tshark**, la
version en ligne de commande de Wireshark, parce que plusieurs zones de
l'interface graphique sont mal restituées par un lecteur d'écran. L'objectif
n'est pas de remplacer tshark, mais de réparer l'interface graphique partout où
l'information existe et n'atteint simplement pas NVDA.

Wireshark 4.6 est construit avec Qt 6 et expose son interface par UI
Automation. Trois familles de défauts en découlent, et toutes trois ont la même
forme : **l'information existe dans l'arbre d'accessibilité, mais pas là où
NVDA la cherche.**

## Ce qui est corrigé

### La liste des interfaces de capture

Sur la page d'accueil, Qt découpe chaque ligne de la liste des interfaces en
une cellule par colonne, et le focus se pose sur une cellule sans texte. NVDA
n'avait donc rien à annoncer, alors que le nom de l'interface se trouvait dans
la cellule voisine de la même ligne.

Les lignes sont désormais annoncées avec le nom de l'interface et la position
dans la liste, par exemple « Wi-Fi, 3 sur 15 ».

### La liste des paquets

Même cause, avec sept colonnes : le focus se pose sur le numéro du paquet, si
bien que NVDA annonçait « 1 », « 2 », « 3 » et rien d'autre.

Les lignes sont maintenant annoncées avec le numéro de trame, la description du
paquet et la position :

> trame 3, 443 &rarr; 58388 [ACK] Seq=1 Ack=2 Win=15, réduit, 3 sur 18

L'horodatage, la source et la destination sont volontairement écartés de cette
annonce automatique. Ce sont de longues suites de chiffres qu'une synthèse
vocale énonce caractère par caractère : coûteuses à l'écoute lorsqu'on parcourt
la liste, et rarement ce dont on a besoin à cet instant. Elles restent à une
touche près, par la commande de lecture de ligne décrite plus bas.

L'état « réduit » est conservé à dessein : il vous indique que la ligne porte
une arborescence de détails, atteignable par Tabulation.

### Les boutons sans nom accessible

Plusieurs boutons de Wireshark n'exposent aucun nom : NVDA n'annonçait que
« bouton ». Leur infobulle, exposée en description, est déjà traduite par
Wireshark : elle est promue en nom, et retirée de la description pour ne pas
être prononcée deux fois.

### Les liens de la page d'accueil

Les liens de la section « Learn » — documentation, wiki, questions et réponses,
listes de diffusion — sont des étiquettes Qt exposées comme du texte statique.
NVDA traite le texte statique comme de la mise en page : il ne disait donc
absolument rien pendant que la Tabulation les traversait. Ils sont désormais
présentés comme des liens et annoncés explicitement.

### Le démarrage et l'arrêt de la capture

Wireshark n'émet **aucun événement d'accessibilité** au démarrage ni à l'arrêt
d'une capture. Deux relevés d'événements distincts l'ont établi : ni changement
de nom, ni changement d'état. `Ctrl+E` annonce maintenant « Démarrage de la
capture » ou « Capture arrêtée ».

### Les coordonnées de tableau dépourvues de sens

Qt expose chaque ligne d'arborescence comme une cellule de tableau, même dans
une arborescence qui n'a qu'une colonne. NVDA annonçait « ligne 1, colonne 1 »
sur chaque champ de l'arborescence des détails du paquet. Ces coordonnées sont
désormais supprimées là où la vue n'a réellement qu'une colonne. Le niveau de
profondeur est conservé : lui distingue un protocole de ses champs.

## Les commandes

Toutes ne sont actives que dans Wireshark, et toutes sont réassignables dans
NVDA, Préférences, Gestes de commandes, catégorie **Wireshark**.

| Raccourci | Effet |
|---|---|
| `Ctrl+E` | Démarre ou arrête la capture, puis annonce le nouvel état |
| `NVDA+Maj+C` | Annonce si une capture est en cours |
| `NVDA+Maj+W` | Lit la ligne courante colonne par colonne, chaque valeur précédée du libellé de sa colonne |
| `NVDA+Maj+E` | Relève dans le journal l'état des commandes de Wireshark |

`Ctrl+E` est transmise à Wireshark avant toute autre chose : son comportement
reste inchangé, quoi que fasse ensuite l'extension.

`NVDA+Maj+W` est là que reviennent les colonnes écartées de l'annonce
automatique :

> No. 1, Time 0.000000000, Source 198.51.100.138, Destination 203.0.113.51,
> Protocol TLSv1.2, Length 104, Info Application Data

Les libellés de colonne sont lus dans l'interface à l'exécution : ils suivent
donc votre propre disposition de colonnes et la langue de votre interface. Ils
ne sont jamais présumés.

### Les commandes de diagnostic, sans raccourci attribué

Trois commandes servent au développement de l'extension. Elles sont
**volontairement dépourvues de raccourci** : un relevé d'accessibilité n'a pas
à pouvoir être déclenché par inadvertance pendant une formation. Assignez-les
dans Gestes de commandes si vous en avez besoin.

* Journalise les informations d'accessibilité de l'objet ayant le focus
* Journalise les informations d'accessibilité de l'objet navigateur
* Active ou désactive la journalisation des événements

## Aucune donnée de capture dans le journal

Aucun relevé n'écrit de données de capture dans le journal de NVDA. Le texte
des lignes de paquets, des détails et des fenêtres de statistiques est remplacé
par un marqueur. Rôles, états, positions, identifiants d'automatisation et
motifs UIA restent en clair, car c'est là ce qui sert au diagnostic. La liste
des interfaces fait exception : elle contient des noms de périphériques, pas du
trafic.

La lecture de ligne, elle, prononce tout : ce qui est à l'écran appartient à
l'utilisateur. Seul le journal est protégé, parce qu'il circule.

## Ce qui n'est pas corrigé, et ne le sera pas

Wireshark dessine le graphique d'activité de la liste des interfaces avec un
delegate et n'en expose **aucune valeur** : ni nom, ni valeur, ni description.
Cette extension n'annonce donc rien à son sujet. Déduire une activité réseau de
l'apparence d'un graphique reviendrait à inventer des données — précisément ce
qu'un technicien réseau ne doit jamais recevoir.

Le débit et le nombre de paquets par interface restent du domaine de tshark.
