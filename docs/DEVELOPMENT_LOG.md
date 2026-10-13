# Historique EXT1

*Note (dépôt public) : les dossiers `development_run_before_context_fix` et
`development_run_comparator_audit` cités ci-dessous ne sont pas inclus dans ce
dépôt, pour limiter son volume. Ce sont des sorties générées, reproductibles à
l'identique en relançant `experiments/run_simulation.py` ; ce journal est
conservé tel quel comme trace honnête du déroulement réel.*

1. Copie de V1 et empreintes de référence, sans modification de l'original.
2. Implémentation d'un filtre à deux contextes et d'une politique à un pas.
3. Un test sans bruit montrait des contextes trop peu séparés (poids ralenti ≈ 0,615). La réversion de vitesse a été renforcée (rho 0,96 → 0,80) et le test a passé. Le premier benchmark est archivé dans development_run_before_context_fix.
4. Audit du comparateur : le filtre adaptatif sans contexte reçoit désormais le même terme d'information qu'EXT1. Cela évite de confondre suppression du contexte et suppression de l'information. La sortie précédente est archivée dans development_run_comparator_audit.
5. Benchmark final de développement : 100 graines par combinaison, 2 400 épisodes. Les graines ont été réutilisées ; aucun statut confirmatoire indépendant n'est revendiqué. Le tutoriel rapporte la réussite similaire du comparateur adaptatif et la faiblesse sous biais.

La variation de durée d'impulsion et la commande myope limitent les conclusions causales. Prochaine étape : comparateurs renforcés et jeu d'évaluation neuf après gel du protocole.
