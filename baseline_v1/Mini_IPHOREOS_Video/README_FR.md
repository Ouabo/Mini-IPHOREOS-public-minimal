# Vidéo pédagogique Mini_IPHOREOS

Vidéo MP4 : 2 min 30, 1280 × 720, sans voix, explications françaises intégrées.
Les traces CSV proviennent du contrôleur original copié sans modification et d’un simulateur reprenant les règles de simulate.py. Le contrôleur ne reçoit jamais la distance réelle.
Le mode prudent est manuel. Les catégories de proximité sont des annotations pédagogiques, pas des concepts appris. Les courbes présentent la croyance ± k écarts-types, pas une garantie de couverture.
Chaque comparaison déroule les essais sur une durée vidéo commune : ce n’est pas une comparaison de temps d’exécution. Le déplacement s’affiche aux instants de mesure ; les impulsions réelles ne sont pas simulées en continu.
La correction du biais de 5 cm est fournie exactement pour illustrer son rôle. Elle n’est pas estimée par cette expérience. Les conclusions concernent un essai illustratif par condition, sans remplacer le benchmark de 3 600 épisodes.
Le manifeste indique la provenance du contrôleur, les paramètres et les résultats. Aucune donnée physique n’est présentée.
Pour reconstruire depuis le dossier de travail initial : python make_mini_iphoreos_video.py (Pillow et imageio-ffmpeg nécessaires).
