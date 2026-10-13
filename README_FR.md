# Mini_IPHOREOS_EXT1 — extension cognitive

Ce dossier est indépendant du projet Mini_IPHOREOS original, qui reste inchangé.

## État actuel

La version 1 a été copiée dans `baseline_v1/` et vérifiée par empreintes SHA-256 (`baseline_manifest.json`). **EXT1 est maintenant implémentée et évaluée en simulation : 2 400 épisodes, six scénarios et quatre politiques. Elle n'est pas validée sur robot physique.**

Commencer par le [tutoriel EXT1 en PDF](Tutorial_EXT1_FR.pdf) ou sa [version HTML](Tutorial_EXT1_FR.html). Les documents de V1 restent inchangés dans `baseline_v1/`.

## Lancer EXT1

Depuis ce dossier :

```powershell
python -B -m pytest -q -p no:cacheprovider tests
python -B experiments/run_simulation.py --trials 100
python tools/build_tutorial.py
```

La simulation remplace les sorties de `results_ext1/`. Le tutoriel nécessite Microsoft Edge et les dépendances indiquées dans `requirements.txt`.

## Résultats à retenir

EXT1 atteint 100% de réussite en régime lent et 97% après ralentissement dans le protocole fourni. Le filtre adaptatif sans contexte discret obtient les mêmes taux : la supériorité propre de la couche contextuelle n'est donc pas établie. Avec un biais inconnu de +5 cm, EXT1 produit 14% de fausses vérifications, contre 1% pour V1 dans ce nouveau protocole. Ces chiffres ne sont pas ceux du benchmark historique V1.

Les catégories conceptuelles et familles de contexte sont prédéfinies ; les paramètres de mouvement sont calibrés et le contexte est inféré en ligne. Le journal est une mémoire d'analyse, pas une mémoire de compétences apprise. Le terme d'information est un proxy gaussien ; aucune implémentation complète d'active inference n'est revendiquée. Le prototype est destiné à Python de bureau, pas directement au micro:bit.

## Organisation

- `baseline_v1/` : référence conservée, avec code, documentation et résultats de la version 1.
- `cognitive/` : filtre de contexte, mémoire d'événements et politique informative.
- `experiments/` : calibration synthétique, scénarios et comparaisons avec la référence.
- `results_ext1/` : sorties propres à l'extension ; ne pas y recopier les résultats V1 comme nouvelles preuves.
- `docs/PLAN_EXTENSION.md` : spécification initiale et critères de validation.
- `development_run_*/` : sorties de développement archivées, à ne pas présenter comme résultats finaux.

Les développements restent dans les nouveaux dossiers en important le contrôleur de référence. Ne pas modifier les fichiers du projet original ni ceux de `baseline_v1/`.

Pour vérifier la référence depuis ce dossier :

```powershell
cd baseline_v1
python -B -m pytest -q -p no:cacheprovider
```

Le simulateur de référence se lance avec `python simulate.py` depuis `baseline_v1/`. Cette commande régénère uniquement les résultats de cette copie locale ; elle ne teste pas encore l'extension.
