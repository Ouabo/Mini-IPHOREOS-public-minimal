# Plan initial de l'extension cognitive

**Mise à jour :** les étapes 1 à 4 existent désormais sous forme d'un prototype de bureau et d'expériences synthétiques. Voir `Tutorial_EXT1_FR.pdf` à la racine pour l'implémentation effective et les limitations. L'apprentissage porte sur des paramètres calibrés, pas sur la découverte de familles conceptuelles. Le diagnostic identifiable du biais et la validation physique restent à réaliser.

## Question scientifique

Un robot peut-il inférer un changement des conditions de déplacement et adapter ses actions plus efficacement que le contrôleur à règles fixes, sous un même budget d'interactions ?

## Sémantique

- **Concepts** : relations prédictives entre impulsion, déplacement et observations. Les familles initiales sont définies par le concepteur ; leurs paramètres seront appris. Aucune découverte autonome de concepts n'est revendiquée à ce stade.
- **Événement intentionnel** : impulsion commandée ou mesure demandée.
- **Événement réalisé** : déplacement compatible avec la prédiction, déplacement insuffisant, observation incohérente ou vérification de cible.
- **Contexte environnemental latent** : dynamique normale ou ralentie. Une hypothèse de biais capteur nécessite une information de calibration identifiable.
- **Préférence de commande** : normal/prudent ; à distinguer du contexte environnemental inféré.

## Modèle proposé

État physique : distance d_t, vitesse effective v_t et, si identifiable, biais b_t. Observations : y_t = d_t + b_t + bruit. Transition : d_(t+1) = d_t − v_t Δt − inertie + bruit de mouvement. Le contexte latent gouverne les paramètres de dynamique. Maintenir une croyance sur l'état et le contexte à partir des seules observations et actions passées.

La vérité du simulateur est réservée à l'évaluation. La distance absolue et un biais constant inconnu ne sont pas séparément identifiables par le seul capteur sans information supplémentaire ; ne pas attribuer au contrôleur une capacité de diagnostic impossible.

## Développement progressif

1. Apprendre le modèle de déplacement sur des essais de calibration séparés.
2. Implémenter un filtre de contexte normal/ralenti, sans fournir les étiquettes au contrôleur.
3. Enregistrer prédictions, actions, observations, erreurs et mises à jour dans une mémoire d'événements.
4. Choisir entre mesure, petite impulsion informative et action orientée vers la cible, avec limites de mouvement conservées.
5. Ajouter ultérieurement une expérience de biais avec référence indépendante explicitement disponible.

## Validation

Séparer calibration, développement et évaluation. Comparer la V1, l'estimation adaptative sans contexte et EXT1, avec mêmes conditions initiales et budgets. Tester changements de vitesse connus du simulateur mais cachés au contrôleur, bruit accru et observations manquantes. Mesurer réussite réelle, fausse vérification, délai de détection, fausses alertes, nombre d'actions et de mesures, temps de calcul et abandons. Rapporter résultats appariés et incertitude sur plusieurs graines. Évaluer une ablation sans action informative. La validation physique reste une étape distincte.

Les hypothèses et seuils définitifs seront documentés avant l'évaluation. Aucun résultat de supériorité n'est présumé.
