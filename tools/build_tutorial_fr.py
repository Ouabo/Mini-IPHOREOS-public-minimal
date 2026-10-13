from pathlib import Path
import csv,json,html
ROOT=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((ROOT/'results_ext1/summary.csv').open()))
def table():
    content='<table><tr><th>Scénario</th><th>V1</th><th>Adaptatif</th><th>EXT1 sans information</th><th>EXT1</th></tr>'
    for scenario in ('normal','slow','switch','recovery','dropout','bias'):
        content+='<tr><td>'+scenario+'</td>'
        for policy in ('v1','adaptive','ext1_no_information','ext1'):
            r=next(r for r in rows if r['scenario']==scenario and r['policy']==policy)
            content+=f"<td>{100*float(r['success']):.0f}%</td>"
        content+='</tr>'
    return content+'</table>'

sections=[('1. EXT1 : ce qui change', '''
<p class="lead">Une architecture cognitive minimale pour estimer, interpréter et agir dans une expérience de distance au mur.</p>
<div class="notice">VERSION EXT1 — prototype Python de bureau, testé en simulation. Aucun déploiement matériel ni apprentissage autonome de nouveaux concepts n'est revendiqué.</div>
<p>Mini_IPHOREOS V1 estime la distance et applique des règles fixes. EXT1 estime conjointement la distance et la vitesse effective, maintient des probabilités sur deux contextes de mouvement et sélectionne une action à l'aide d'un objectif combinant progression, coût et information.</p>
<table><tr><th>V1 conservée</th><th>Extension EXT1</th></tr><tr><td>Distance scalaire</td><td>Distance et vitesse, incertitude conjointe</td></tr><tr><td>Normal/prudent : réglage manuel</td><td>Normal/ralenti : hypothèses environnementales inférées</td></tr><tr><td>Règles de déplacement</td><td>Comparaison d'actions candidates</td></tr><tr><td>État courant</td><td>Journal de croyances et d'événements</td></tr></table>
<p>Le prototype cible 25 cm et accepte la bande 21–29 cm. La vérité physique appartient au simulateur ; le contrôleur reçoit uniquement les mesures bruitées, le temps et les paramètres de calibration.</p>
<h2>Préservation des versions</h2><p><code>baseline_v1/</code> contient la copie de référence. Ses fichiers et ceux du projet original sont contrôlés par empreintes SHA-256. L'extension utilise <code>cognitive/</code>, <code>experiments/</code> et <code>results_ext1/</code>. Ce tutoriel remplace uniquement la documentation d'entrée d'EXT1 ; celui de V1 reste dans son dossier.</p>
'''),('2. Concepts, événements et contextes', '''
<div class="flow">Observation → croyance distance/vitesse → relations prédictives → option choisie → observation suivante → événement réalisé</div>
<h2>Concepts opérationnels</h2><p>Deux relations sont explicites dans la mémoire : « la cible est compatible avec ma croyance » et « cette impulsion devrait produire ce déplacement ». Leurs formes sont définies par le concepteur ; la calibration estime les vitesses et la boucle ajuste les croyances. Le système ne découvre pas de vocabulaire conceptuel.</p>
<h2>Événement intentionnel et événement réalisé</h2><p><code>intended_option</code> vaut MOVE, SAMPLE, DONE ou ABORT. <code>realised_event</code> décrit la lecture initiale, une observation après mouvement, une lecture stationnaire, une conséquence inattendue, une mesure inutilisable ou une vérification. « Mouvement observé » signifie ici qu'une observation suit la commande ; il ne prouve pas un déplacement mesuré indépendamment.</p>
<h2>Contexte inféré</h2><p>Les familles normal et ralenti sont prédéfinies, avec vitesses calibrées proches de 8 et 3 cm/s. Le filtre met à jour leurs probabilités. Il ne reçoit pas le contexte réel du simulateur. La famille choisie n'est pas une certitude ; un changement doit s'accumuler dans les observations.</p>
<p>Le réglage prudent de V1 est une préférence de commande, pas une hypothèse sur le sol. EXT1 ne confond pas ces notions. Une faible vitesse peut avoir plusieurs causes physiques : le modèle infère une dynamique ralentie, sans diagnostiquer nécessairement un sol glissant.</p>
<h2>Mémoire</h2><p>Le journal relie l'observation, la croyance, l'option et la conséquence. Il sert à l'analyse ; aucune mémoire de compétences inter-épisodes, aucun rejeu d'apprentissage ni composition d'événements à long horizon n'est encore implémenté.</p>
'''),('3. Modélisation et estimation', '''
<p>L'état est <b>x = (d, v)</b>, distance et vitesse. Le contexte discret est normal ou ralenti. Une distribution gaussienne est maintenue pour chaque contexte, puis combinée par pondération.</p>
<div class="equation">d′ = d − v Δt − c + bruit<br>v′ = ρv + (1 − ρ)m<sub>contexte</sub> + bruit<br>y = d + b + bruit de mesure</div>
<p>c est l'inertie moyenne ; b est le biais calibré. Le prototype fixe ρ = 0,80 pour les modèles contextuels. À chaque mouvement, une matrice de transition avec diagonale 0,96 autorise un changement de contexte. Les mises à jour utilisent mélange des moments, prédiction linéaire et correction de Kalman ; les vraisemblances normalisées actualisent les poids des contextes. Les lectures stationnaires ne provoquent pas artificiellement des transitions de contexte.</p>
<p>La calibration synthétique est séparée : graine 1701, 160 mesures à quatre distances et 80 impulsions par famille de vitesse. Les étiquettes sont disponibles en calibration supervisée, jamais au contrôleur pendant l'évaluation. Le script estime biais, variance capteur, vitesses et inertie. La variance de mouvement de 0,04 cm² et les autres hyperparamètres restent des choix de prototype, non une calibration matérielle.</p>
<div class="notice">Identifiabilité : avec un seul capteur y = d + b + bruit, une distance absolue et un biais constant inconnus peuvent rester confondus. EXT1 ne prétend pas apprendre ce biais sans référence supplémentaire.</div>
<p>La covariance jointe permet aux déplacements suivis de mesures d'informer la vitesse. Les tests vérifient sa positivité, la normalisation des probabilités et le fait que répéter des lectures immobiles ne révèle pas une vitesse inconnue.</p>
'''),('4. Décision et limites de contrôle', '''
<p>À chaque lecture valide, les candidats sont : mesurer sans bouger, impulsion de 0,12 s, impulsion de 0,24 s. Une impulsion est éliminée si sa borne basse prédite, après marge d'incertitude et réserve de 0,5 cm, descend sous 21 cm.</p>
<div class="equation">Score = [(distance prédite − 25)² + variance prédite] / 400<br>+ 0,08 × coût temporel − 0,8 × information attendue sur la vitesse</div>
<p>L'information est un proxy gaussien : la moitié du logarithme du rapport entre variance de vitesse avant et après une prochaine mesure hypothétique. Il ne s'agit ni d'une information mutuelle exacte sur le contexte, ni d'une implémentation complète de l'énergie libre attendue. Le planificateur est à un pas ; il n'effectue pas de recherche hiérarchique à long horizon.</p>
<p>Trois lectures compatibles avec |distance estimée − 25| + 1,64 écart-type ≤ 4 conduisent à DONE. Elles sont corrélées et ne constituent pas trois validations indépendantes. Trois mesures invalides ou incompatibles conduisent à ABORT. L'expérience impose aussi 80 s, 100 mouvements et 350 décisions au maximum.</p>
<p>Le contrôle de risque repose sur le modèle. Un biais peut invalider ces marges. Aucun certificat de sécurité physique n'est fourni.</p>
<h2>Ablation importante</h2><p>Sans terme d'information, le score myope peut préférer attendre et rester bloqué à proximité de la cible en régime lent. Les mauvais résultats de cette ablation décrivent cette fonction de coût précise ; ils ne démontrent pas que toute commande sans recherche d'information échoue.</p>
'''),('5. Exécuter et explorer', '''
<p>Ouvrir PowerShell dans <code>Mini_IPHOREOS_EXT1</code>. L'environnement actuel dispose déjà de NumPy, Matplotlib et pytest. Pour une nouvelle installation :</p>
<pre>python -m pip install -r requirements.txt
python -B -m pytest -q -p no:cacheprovider tests
python -B experiments/run_simulation.py --trials 100</pre>
<p>La dernière commande écrit 2 400 épisodes dans <code>results_ext1/</code> : six scénarios, quatre politiques, cent graines par combinaison. Elle remplace les résultats EXT1 antérieurs, jamais ceux de V1. Les durées CPU varient selon la machine.</p>
<table><tr><th>Fichier</th><th>Usage</th></tr><tr><td>calibration*.csv / json</td><td>Données synthétiques et paramètres estimés</td></tr><tr><td>trials.csv</td><td>Une ligne par épisode, y compris échecs</td></tr><tr><td>summary.csv</td><td>Résultats agrégés</td></tr><tr><td>paired_success_differences.csv</td><td>Contrastes appariés exploratoires</td></tr><tr><td>trace_*.json</td><td>Mémoire et vérité du simulateur pour la graine 10000</td></tr><tr><td>comparison.png</td><td>Réussite et fausse vérification</td></tr><tr><td>manifest.json</td><td>Graines, limites et empreintes des sources</td></tr></table>
<p>Pour lire une trace, distinguer les champs <code>simulator_*</code> des données accessibles au contrôleur. Le journal ajoute ces champs après la décision pour l'évaluation.</p>
<pre>python tools/build_tutorial.py</pre><p>Cette commande reconstruit le tutoriel HTML et PDF après une nouvelle simulation. Elle nécessite Playwright, PyMuPDF et Microsoft Edge. Le code EXT1 dépend de NumPy : ne pas copier ces fichiers directement sur le micro:bit.</p>
'''),('6. Résultats et interprétation', '''
<p>Réussite = DONE et distance réelle entre 21 et 29 cm. Pourcentage observé sur 100 essais par case :</p>'''+table()+'''
<img src="results_ext1/comparison.png" alt="Comparaison des taux de réussite et fausse vérification">
<p><b>Résultat principal :</b> EXT1 s'adapte aux dynamiques lentes mieux que la référence V1 dans ce simulateur. Mais le filtre adaptatif sans contexte discret, doté du même terme d'information, obtient également 100% en régime lent et 97% après ralentissement. Ces résultats n'établissent donc pas un avantage propre de la couche contextuelle sur cette alternative.</p>
<p>Avec biais inconnu, EXT1 atteint 86% de réussite et 14% de fausses vérifications, contre 99% et 1% pour V1 dans ce protocole. La meilleure précision nominale ne supprime pas la vulnérabilité au biais.</p>
'''),('7. Portée scientifique et validation suivante', '''
<p>V1 utilise une impulsion fixe de 0,12 s ; les trois politiques adaptatives accèdent à 0,12 et 0,24 s. Les gains de temps ou de nombre d'actions face à V1 combinent donc adaptation et changement d'actions disponibles. La comparaison adaptatif/EXT1 isole mieux la contribution du contexte. Les calculs d'EXT1 sont plus coûteux ; moins de mouvements ne signifie pas moins de calcul.</p>
<p>Les contextes ont une mémoire : en scénario recovery, un poids élevé du contexte lent peut persister après le retour à la normale. La colonne false_context_alert inclut ce retard transitoire ; ce n'est pas uniquement une alarme spontanée. Les zéros pour les politiques sans contexte ne constituent pas des performances de détection. Le délai de changement est disponible par essai dans trials.csv.</p>
<p>Les intervalles bootstrap appariés sont descriptifs, sans correction de multiplicité. Des résultats identiques peuvent produire un intervalle dégénéré : 100 succès ne prouvent pas une probabilité de réussite égale à 1. Les graines ont été réutilisées après une correction de test et une correction du comparateur ; il s'agit d'un développement exploratoire, pas d'une validation confirmatoire indépendante.</p>
<h2>Étapes suivantes</h2><ol><li>Comparer les politiques avec exactement les mêmes durées d'impulsion autorisées et une commande prédictive plus forte.</li><li>Fixer les paramètres sur un ensemble de développement, puis tester des graines et dynamiques non utilisées.</li><li>Évaluer transitions répétées, régimes intermédiaires et changements hors des deux familles prévues.</li><li>Ajouter une référence indépendante avant toute revendication de diagnostic du biais.</li><li>Calibrer le robot réel, adapter le logiciel au matériel puis exécuter des essais supervisés indépendants.</li></ol>
<p>Pour le montage, les connexions et la calibration physique, consulter le tutoriel V1 dans baseline_v1. Ce document ne modifie pas ses programmes moteurs. La version actuelle d'EXT1 est exclusivement une preuve de fonctionnement logiciel.</p>
''')]
css='''@page{size:A4;margin:17mm}body{font:11pt Arial;color:#172a40;margin:0}section{break-after:page}section:last-child{break-after:auto}h1{font-size:23pt;color:#126b70;margin:10px 0 20px}h2{font-size:14pt;margin-top:24px}p,li{line-height:1.45}table{border-collapse:collapse;width:100%;font-size:10pt;margin:15px 0}td,th{padding:9px;border:1px solid #c8d7df;text-align:left}th{background:#e3f0f2}.notice{padding:14px;background:#fff0d0;border-left:4px solid #dd9b24;margin:18px 0}.flow,.equation{padding:18px;background:#e6f3f1;line-height:1.7}pre{white-space:pre-wrap;background:#edf1f5;padding:14px;font-size:10pt}code{font-size:9.5pt;overflow-wrap:anywhere}img{width:100%}.tag{font-size:9pt;color:#597485;letter-spacing:1px}.lead{font-size:15pt} @media screen{body{max-width:820px;margin:30px auto;padding:20px}section{margin-bottom:65px}}'''
document='<!doctype html><html lang="fr"><meta charset="utf-8"><title>Mini_IPHOREOS_EXT1 — Tutoriel</title><style>'+css+'</style><body>'+''.join('<section><div class="tag">MINI_IPHOREOS_EXT1 • ARCHITECTURE COGNITIVE • SIMULATION</div><h1>'+title+'</h1>'+body+'</section>' for title,body in sections)+'</body></html>'
(ROOT/'Tutorial_EXT1_FR.html').write_text(document,encoding='utf-8')
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,channel='msedge');page=browser.new_page()
    page.goto((ROOT/'Tutorial_EXT1_FR.html').as_uri());page.emulate_media(media='print')
    page.pdf(path=str(ROOT/'Tutorial_EXT1_FR.pdf'),format='A4',print_background=True,prefer_css_page_size=True)
    browser.close()
import fitz
doc=fitz.open(ROOT/'Tutorial_EXT1_FR.pdf')
report={'pages':len(doc),'words':sum(len(p.get_text().split()) for p in doc),'outside':[]}
for i,p in enumerate(doc):
    for b in p.get_text('blocks'):
        if b[0]<0 or b[1]<0 or b[2]>p.rect.width+1 or b[3]>p.rect.height+1:report['outside'].append(i+1)
doc[0].get_pixmap().save(ROOT/'docs/tutorial_preview.png')
(ROOT/'docs/tutorial_verification.json').write_text(json.dumps(report,indent=2))
print(report)
