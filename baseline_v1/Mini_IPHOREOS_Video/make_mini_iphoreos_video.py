from pathlib import Path
import sys, random, json, csv, hashlib, shutil, math
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.video_dependencies'))
import imageio_ffmpeg
OUT=ROOT/'Mini_IPHOREOS_Video'; OUT.mkdir(exist_ok=True)
SOURCE=Path(r'C:\Users\flore\Desktop\Electricity_IntraDay_project\Project_Robotic\Mini_IPHOREOS\firmware\belief_controller.py')
shutil.copy2(SOURCE,OUT/'belief_controller.py')
sys.path.insert(0,str(OUT))
from belief_controller import Controller

def episode(context='normal',bias=None,correction=0):
    seed=7; init=random.Random(seed); sensor=random.Random(seed+100000); motion=random.Random(seed+200000)
    distance=init.uniform(45,85); speed=init.uniform(6.8,9.2)
    nominal_bias=init.uniform(-.6,.6); bias=nominal_bias if bias is None else bias
    c=Controller('mini',context,{'sensor_bias_cm':correction}); t=0; rows=[]
    for i in range(600):
        u=sensor.random(); noise=sensor.gauss(0,1.6)
        raw=None if u<.02 else distance+bias+noise+(12 if .02<=u<.03 else 0)
        action=c.observe(raw,t)
        rows.append(dict(time=t,true=distance,raw=raw,mu=c.mu,sd=math.sqrt(c.var),action=action,reason=c.reason,verify=c.verify,context=context,k=c.k))
        if action in ('DONE','ABORT'): break
        if action=='MOVE':
            distance-=max(0,speed*.12+.15+motion.gauss(0,.20));c.record_move(.12);t+=.32
        else:t+=.15
    return rows

runs={'normal':episode(),'prudent':episode('careful'),'biais':episode(bias=5),'corrige':episode(bias=5,correction=5)}
for name,rows in runs.items():
    with (OUT/f'trace_{name}.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)

FONT=Path('C:/Windows/Fonts')
def font(n,bold=False):return ImageFont.truetype(str(FONT/('arialbd.ttf' if bold else 'arial.ttf')),n)
BG='#0b1425'; CARD='#14233a'; WHITE='#eff5ff'; MUTED='#a9bad1'; TEAL='#49dbc3'; GOLD='#ffcd70'; RED='#ff7f88'
def text(draw,xy,t,size=24,color=WHITE,bold=False):draw.text(xy,t,font=font(size,bold),fill=color)
def lines(draw,xy,t,size=24,color=WHITE,gap=10):
    x,y=xy
    for line in t.split('\n'):text(draw,(x,y),line,size,color);y+=size+gap
def base(title,sub,chapter):
    im=Image.new('RGB',(1280,720),BG);d=ImageDraw.Draw(im)
    text(d,(36,23),'MINI_IPHOREOS  /  SIMULATION EXPLICATIVE',17,TEAL,True)
    text(d,(36,56),title,34,WHITE,True);text(d,(36,103),sub,19,MUTED)
    text(d,(36,684),'Logiciel réel • données synthétiques • aucune validation physique',17,MUTED)
    text(d,(1090,684),chapter,17,TEAL)
    return im,d
LABEL={'MOVE':'AVANCER','SAMPLE':'MESURER','DONE':'TERMINÉ','ABORT':'ABANDON'}
REASON={'short_forward_pulse':'Une courte impulsion est autorisée.','verify_target_band':'Vérification de la zone cible.','uncertain_next_step':'Incertitude : mesurer avant de bouger.','estimate_near_or_below_target':'Proche de la cible : reprendre une mesure.','invalid_sensor':'Mesure invalide : nouvelle lecture.','inconsistent_observation':'Observation incohérente avec le modèle.','inconclusive_after_sampling':'Trop de lectures sans conclusion.'}
def panel(d,box,title,rows,progress):
    x,y,w,h=box; d.rounded_rectangle((x,y,x+w,y+h),16,fill=CARD)
    text(d,(x+20,y+15),title,23,WHITE,True)
    elapsed=progress*rows[-1]['time'];idx=max(i for i,r in enumerate(rows) if r['time']<=elapsed+1e-9);r=rows[idx]
    text(d,(x+20,y+48),f"Contexte manuel : {'prudent' if r['context']=='careful' else 'normal'}  |  k = {r['k']}",17,TEAL)
    left=x+40;right=x+w-40; scale=(right-left)/90
    # Real simulator distance is deliberately separate from robot belief.
    def sx(v):return right-v*scale
    sy=y+123
    d.rectangle((sx(29),sy-28,sx(21),sy+32),fill='#20564e')
    d.line((right,sy-38,right,sy+37),fill=WHITE,width=6)
    rx=sx(r['true']);d.rounded_rectangle((rx-46,sy-18,rx,sy+18),5,fill=GOLD)
    d.ellipse((rx-40,sy-24,rx-26,sy-12),fill=MUTED);d.ellipse((rx-40,sy+12,rx-26,sy+24),fill=MUTED)
    d.line((rx,sy,right,sy),fill=GOLD,width=2)
    text(d,(left,sy+45),f"Vérité du simulateur : {r['true']:.1f} cm",19,GOLD)
    text(d,(left,sy+69),'Non accessible au contrôleur',15,MUTED)
    mu=r['mu']; sd=r['sd']
    text(d,(left,y+225),f"Estimation : {mu:.1f} cm  |  écart-type : {sd:.2f} cm",19,TEAL)
    concept='ZONE CIBLE ESTIMÉE' if abs(mu-25)<=4 else ('LOIN DE LA CIBLE' if mu>29 else 'TROP PROCHE')
    text(d,(left,y+258),'CONCEPT : '+concept,17,WHITE,True)
    text(d,(left,y+285),'Catégorie prédéfinie, pas un concept appris',15,MUTED)
    # History with truth, estimate and uncertainty band.
    gx=left; gy=y+332;gw=w-80;gh=75
    d.line((gx,gy+gh,gx+gw,gy+gh),fill=MUTED)
    def point(j,v):return (gx+gw*rows[j]['time']/max(rows[-1]['time'],.01),gy+gh*(1-(v-10)/80))
    if idx>0:
        upper=[point(j,rows[j]['mu']+rows[j]['k']*rows[j]['sd']) for j in range(idx+1)]
        lower=[point(j,rows[j]['mu']-rows[j]['k']*rows[j]['sd']) for j in range(idx,-1,-1)]
        d.polygon(upper+lower,fill='#21504e')
        d.line([point(j,rows[j]['true']) for j in range(idx+1)],fill=GOLD,width=2)
        d.line([point(j,rows[j]['mu']) for j in range(idx+1)],fill=TEAL,width=2)
    text(d,(gx,gy+gh+5),'Or : réalité   •   Vert : croyance ± k écart-types',14,MUTED)
    text(d,(left,y+444),'DÉCISION : '+LABEL[r['action']],22,TEAL if r['action']!='ABORT' else RED,True)
    text(d,(left,y+476),REASON.get(r['reason'],r['reason']),16,WHITE)
    text(d,(left,y+501),f"Événement : lecture {idx+1}  |  vérifications : {r['verify']}/3",16,MUTED)
    return r

def frame(t):
    if t<12:
        im,d=base('Un robot qui mesure, agit et vérifie','Une expérience simple pour comprendre les limites de la confiance.', '1 / 5')
        lines(d,(65,177),'MISSION\nApprocher un mur et s’arrêter à 25 cm.\nZone acceptable : de 21 à 29 cm.',29,WHITE,16)
        lines(d,(65,371),'CONCEPT : une propriété, par exemple « proche ».\nÉVÉNEMENT : une mesure, un mouvement, une vérification.\nCONTEXTE : un réglage qui change les marges de décision.',25,TEAL,20)
        text(d,(65,578),'Ici, concepts et contextes sont définis par le concepteur.',22,GOLD)
    elif t<49:
        im,d=base('01  /  Observer la boucle de décision','Le même contrôleur que dans le projet produit chaque décision.', '2 / 5')
        panel(d,(30,145,720,530),'Approche nominale — essai fixé : graine 7',runs['normal'],min(1,(t-12)/30))
        lines(d,(780,174),'1. MESURER\nLe capteur est bruité.\n\n2. ESTIMER\nDistance + incertitude.\n\n3. AGIR\nPetite impulsion ou attente.\n\n4. VÉRIFIER\nTrois lectures positives.',23,WHITE,8)
        text(d,(780,595),'Temps ralenti pour expliquer.',17,GOLD)
    elif t<91:
        im,d=base('02  /  Le contexte modifie la prudence','Conditions initiales et flux aléatoires appariés ; actions potentiellement différentes.', '3 / 5')
        p=min(1,(t-49)/34)
        panel(d,(25,145,605,530),'Mode normal',runs['normal'],p)
        panel(d,(650,145,605,530),'Mode prudent',runs['prudent'],p)
    elif t<133:
        im,d=base('03  /  Un capteur biaisé peut tromper le robot','Biais réel +5 cm. À droite : correction connue fournie, non apprise automatiquement.', '4 / 5')
        p=min(1,(t-91)/33)
        a=panel(d,(25,145,605,530),'Sans correction du biais',runs['biais'],p)
        panel(d,(650,145,605,530),'Avec correction de +5 cm',runs['corrige'],p)
        if p==1:
            verdict='FAUSSE VÉRIFICATION' if a['action']=='DONE' and abs(a['true']-25)>4 else 'Comparer décision et position réelle'
            d.rectangle((35,312,620,343),fill='#70343d');text(d,(45,315),verdict,21,WHITE,True)
    else:
        im,d=base('Ce que Mini_IPHOREOS démontre','Une première brique expérimentale, pas encore l’architecture cognitive complète.', '5 / 5')
        lines(d,(65,170),'IMPLÉMENTÉ\nEstimation de distance et incertitude.\nActions courtes, nouvelles mesures, vérification et arrêt.',26,TEAL,15)
        lines(d,(65,325),'À DÉVELOPPER DANS IPHOREOS\nConcepts appris • contexte inféré • événements réutilisables.\nCalibration et validation sur le robot physique.',26,WHITE,15)
        lines(d,(65,500),'LEÇON : une croyance précise peut être fausse.\nUne vérification indépendante reste nécessaire.',29,GOLD,18)
    return im

fps=12;duration=150
writer=imageio_ffmpeg.write_frames(str(OUT/'Mini_IPHOREOS_Explication_FR.mp4'),(1280,720),fps=fps,codec='libx264',pix_fmt_in='rgb24',pix_fmt_out='yuv420p',quality=7,macro_block_size=16)
writer.send(None)
for i in range(duration*fps):
    im=frame(i/fps)
    writer.send(im.tobytes())
    if i in (240,840,1488):im.save(OUT/f'apercu_{i//fps}s.png')
    if i%(fps*30)==0:print(f'Video: {i//fps}/{duration}s',flush=True)
writer.close()
manifest={'duration_seconds':duration,'fps':fps,'resolution':[1280,720],'seed':7,'controller_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'results':{k:{'terminal':v[-1]['action'],'true_final_cm':v[-1]['true'],'false_verification':v[-1]['action']=='DONE' and abs(v[-1]['true']-25)>4} for k,v in runs.items()},'notes':'Silent French captioned simulation. Manual contexts and predefined concepts. Known bias correction is illustrative, not physical calibration. Same fixed seed selected before inspecting outcomes. Comparison playback normalised per episode.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
shutil.copy2(__file__,OUT/Path(__file__).name)
(OUT/'README_FR.md').write_text('''# Vidéo pédagogique Mini_IPHOREOS

Vidéo MP4 : 2 min 30, 1280 × 720, sans voix, explications françaises intégrées.
Les traces CSV proviennent du contrôleur original copié sans modification et d’un simulateur reprenant les règles de simulate.py. Le contrôleur ne reçoit jamais la distance réelle.
Le mode prudent est manuel. Les catégories de proximité sont des annotations pédagogiques, pas des concepts appris. Les courbes présentent la croyance ± k écarts-types, pas une garantie de couverture.
Chaque comparaison déroule les essais sur une durée vidéo commune : ce n’est pas une comparaison de temps d’exécution. Le déplacement s’affiche aux instants de mesure ; les impulsions réelles ne sont pas simulées en continu.
La correction du biais de 5 cm est fournie exactement pour illustrer son rôle. Elle n’est pas estimée par cette expérience. Les conclusions concernent un essai illustratif par condition, sans remplacer le benchmark de 3 600 épisodes.
Le manifeste indique la provenance du contrôleur, les paramètres et les résultats. Aucune donnée physique n’est présentée.
Pour reconstruire depuis le dossier de travail initial : python make_mini_iphoreos_video.py (Pillow et imageio-ffmpeg nécessaires).
''',encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False),flush=True)
