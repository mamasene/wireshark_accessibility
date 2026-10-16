# Protocole de relevé d'accessibilité

Objectif : établir **ce que Wireshark expose réellement à NVDA**, sans supposer
la structure de son interface. Aucun code correctif n'est écrit avant le relevé.

Ce protocole a servi à chaque correction livrée. Il sert désormais à instruire
les zones restantes de Wireshark.

## 0. Préparation

1. Installer l'extension : NVDA, Outils, Magasin d'extensions, Installer depuis
   un fichier externe, puis choisir le `.nvda-addon`. Redémarrer NVDA.
2. Les trois commandes de relevé **n'ont aucun raccourci attribué**. Les
   assigner dans NVDA, Préférences, Gestes de commandes, catégorie
   « Wireshark » :
   * *Journalise les informations d'accessibilité de l'objet ayant le focus* ;
   * *Journalise les informations d'accessibilité de l'objet navigateur* ;
   * *Active ou désactive la journalisation des événements*.
3. Régler le niveau de journalisation sur **Débogage** : NVDA, Préférences,
   Paramètres, Avancé.
4. Ouvrir l'observateur de journal : NVDA, Outils, Observateur de journal.

> Les blocs de relevé sont encadrés dans le journal par
> `=== WIRESHARK-DIAG DEBUT/FIN : <titre> ===`, ce qui permet de les retrouver
> sans les lire en entier. Le journal se trouve dans `%TEMP%\nvda.log`, la
> session précédente dans `nvda-old.log`.

## 1. Ce que les relevés contiennent, et ce qu'ils taisent

Les relevés décrivent la **structure** : rôle, états, position, nombre
d'enfants, identifiant d'automatisation, nom de classe Qt, motifs UIA,
hiérarchie des parents, frères immédiats.

Le **texte des cellules d'arborescence est masqué** — lignes de paquets,
détails, statistiques. Un journal circule : il ne doit pas transporter
d'adresses, de ports ni de charges utiles. La liste des interfaces fait
exception, elle ne contient que des noms de périphériques.

Pour entendre le contenu réel d'une ligne sans l'écrire nulle part, utiliser la
commande de lecture de ligne, `NVDA+Maj+W`.

## 2. Relevés à effectuer sur une zone nouvelle

| # | Cible | Action |
|---|-------|--------|
| 1 | Le conteneur | Placer le focus sur la zone, puis la commande de relevé du focus |
| 2 | Un élément correctement annoncé | S'y placer, puis relevé du focus |
| 3 | Un élément annoncé vide ou incomplet | S'y placer, puis relevé du focus |
| 4 | Un élément sélectionné ou actif | S'y placer, puis relevé du focus |
| 5 | Un élément inatteignable au clavier | Navigation par objets, puis relevé de l'objet navigateur |
| 6 | Les événements | Activer la journalisation, exercer la zone, désactiver |
| 7 | Les commandes et leurs états | `NVDA+Maj+E`, une fois dans chaque état à distinguer |

Le relevé 7 est celui qui a permis d'annoncer le démarrage et l'arrêt de la
capture : comparer deux états de l'interface fait apparaître le repère
exploitable, là où aucun événement n'existe.

## 3. Grille du comportement clavier

À remplir à l'oreille, hors relevés techniques. C'est elle qui distingue un
défaut d'annonce d'un défaut de navigation.

| Touche | Ce que NVDA annonce | Ce qui se passe visuellement |
|---|---|---|
| Tabulation | | |
| Maj+Tabulation | | |
| Flèche bas / haut | | |
| Début / Fin | | |
| Entrée | | |
| Contrôle+Alt+flèches | | |
| `NVDA+Tab` | | |

## 4. Vérification croisée avec le modèle d'affichage

Sur un élément annoncé vide :

1. Placer l'objet navigateur dessus.
2. Basculer le curseur de revue en **revue écran**, puis lire la ligne.
3. Noter si le texte est lisible à l'écran alors qu'il est absent de l'arbre
   d'accessibilité.

C'est la distinction décisive : un élément **vide** ne contient rien ; un
élément **non exposé** contient quelque chose que NVDA ne peut pas atteindre.
Le premier relève de Wireshark, le second peut souvent être corrigé ici.

## 5. Console Python de NVDA

`NVDA+Contrôle+Z`, puis :

```python
focus.name, focus.role, focus.states
focus.parent.name, focus.parent.role, focus.parent.childCount
[(c.name, c.role) for c in focus.parent.children][:5]
focus.appModule.productName, focus.appModule.productVersion
type(focus).__mro__
```

`type(focus).__mro__` répond à une question précise : la classe de correction de
l'extension est-elle bien greffée sur cet objet ? Elle a servi plusieurs fois à
distinguer « ma correction ne s'applique pas » de « ma correction s'applique et
ne suffit pas ».

## 6. Si NVDA ne suffit pas

**Accessibility Insights for Windows**, ou **Inspect.exe** du SDK Windows en
basculant entre les modes *UI Automation* et *MSAA* : cela distingue ce que Qt
n'expose pas du tout de ce que NVDA n'exploite pas.

Relever : `ControlType`, `Name`, `AutomationId`, `ClassName`,
`LocalizedControlType`, `IsSelectionItemPatternAvailable`,
`SelectionItem.IsSelected`, `LegacyIAccessible.Name`, `GridItem.Row`,
`GridItem.Column`.

## 7. Règle de décision

Avant d'écrire une correction, classer le constat :

| Catégorie | Suite à donner |
|---|---|
| Déjà exposé correctement | Rien à faire |
| Présent dans un objet voisin, non annoncé | Corrigeable par l'App Module |
| Rôle inadapté qui fait traiter du contenu comme de la mise en page | Corrigeable par l'App Module |
| Présent visuellement, absent de l'arbre | À remonter en amont ; **rien ne sera inventé** |
| Nécessiterait les données de Wireshark | Domaine de tshark |

La quatrième ligne est la plus importante. Un technicien réseau ne doit jamais
recevoir une valeur déduite de l'apparence d'un graphique.
