"""Editable schematic illustrations and the cost workbook (CSV/JSON)."""
from pathlib import Path
import csv,json,html
R=Path(__file__).resolve().parents[1];A=R/'assets';A.mkdir(exist_ok=True)
NAVY='#0F1E2E';TEAL='#0D8080';AMBER='#C97200';ICE='#EEF5F5'
def svg(name,title,body,height=400):
    text=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{height}" viewBox="0 0 1100 {height}"><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="{TEAL}"/></marker></defs><rect width="1100" height="{height}" fill="white"/><style>text{{font-family:Arial,sans-serif;fill:{NAVY}}}.title{{font-size:27px;font-weight:bold}}.label{{font-size:21px;font-weight:bold}}.small{{font-size:18px}}.note{{font-size:16px;fill:#526c7c}}</style><text x="30" y="40" class="title">{html.escape(title)}</text>{body}</svg>'''
    (A/(name+'.svg')).write_text(text,encoding='utf-8')
def box(x,y,w,h,title,lines=(),fill=ICE):
    s=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="#bfd3d7"/><text x="{x+18}" y="{y+32}" class="label">{html.escape(title)}</text>'
    for i,line in enumerate(lines):s+=f'<text x="{x+18}" y="{y+62+i*25}" class="small">{html.escape(line)}</text>'
    return s
def arrow(x1,y1,x2,y2): return f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{TEAL}" stroke-width="3" marker-end="url(#arrow)"/>'

svg('parts','Buy one robot kit, one brain and four AA cells',
    box(30,80,325,200,':MOVE Motor 5683',['Chassis + two wheels','Motors + motor electronics','Ultrasonic sensor','Built-in AA holders'])+
    box(390,80,320,200,'micro:bit V2 Go',['Onboard computer','USB data cable included','Bundle AAA cells are','not the robot AA supply'])+
    box(745,80,325,200,'Simple test equipment',['4 matched AA cells','Ruler / tape measure','Wide cardboard target','Floor tape; your laptop'])+
    '<text x="35" y="330" class="note">No separate motor driver, breadboard, camera, soldering iron or 3D printer is needed for this build.</text>',370)
svg('power_signal','How software reaches the wheels',
    box(30,90,210,135,'Laptop',['Write MicroPython','USB transfers code'])+arrow(245,155,285,155)+
    box(290,90,225,135,'micro:bit V2',['Run belief + policy','Send motor requests'])+arrow(520,155,560,155)+
    box(565,90,225,135,'Motor electronics',['Switch battery power','Drive two motors'])+arrow(795,155,835,155)+
    box(840,90,230,135,'Wheels',['Robot moves','Distance changes'])+
    box(565,265,225,80,'4 AA batteries')+arrow(677,260,677,230)+
    '<path d="M950,230 L950,375 L402,375 L402,230" fill="none" stroke="#C97200" stroke-width="3" marker-end="url(#arrow)"/><text x="450" y="365" class="small">Ultrasonic measurement closes the loop</text>',420)
svg('assembly','Assembly: power off; use the supplied orientation guide',
    box(30,85,325,170,'1 / Fit the wheels',['Press each wheel onto','its motor shaft as shown','in the kit booklet.'])+
    box(390,85,320,170,'2 / Insert micro:bit',['Align the edge connector','using the manufacturer','picture; never force it.'])+
    box(745,85,325,170,'3 / Fit four AA cells',['Match + and - markings.','Do not connect the separate','AAA pack at the same time.'])+
    '<text x="35" y="315" class="label">First power-on: sensor-only firmware; robot stationary; physical switch accessible.</text><text x="35" y="350" class="note">This schematic explains the order, not exact connector orientation or component placement.</text>',390)
svg('track','Your experiment: one straight approach on the floor',
    '<rect x="30" y="80" width="1040" height="230" rx="12" fill="#f5f1e9"/><rect x="950" y="90" width="40" height="190" fill="#bb9360"/><text x="895" y="330" class="label">Cardboard wall</text><rect x="140" y="160" width="130" height="85" rx="12" fill="#0D8080"/><rect x="150" y="140" width="35" height="25" fill="#0F1E2E"/><rect x="150" y="240" width="35" height="25" fill="#0F1E2E"/><circle cx="265" cy="190" r="13" fill="#ccc"/><circle cx="265" cy="220" r="13" fill="#ccc"/>'+arrow(300,203,580,203)+
    '<rect x="650" y="105" width="100" height="170" fill="#17c4b0" opacity=".2"/><line x1="700" y1="100" x2="700" y2="280" stroke="#0D8080" stroke-width="3" stroke-dasharray="7"/><text x="630" y="130" class="small">Target band</text><path d="M700,295 L950,295" stroke="#0F1E2E" stroke-width="2"/><text x="755" y="325" class="small">25 cm target</text><text x="50" y="360" class="note">Measure from the ultrasonic sensor face to the wall. Start at 45–85 cm. Band: 21–29 cm. Diagram not to scale.</text>',390)
svg('upload','From a Python file to the onboard computer',
    box(30,85,325,180,'1 / Open one file',['flash/01_sensor_only.py','Review settings near the top.','Motors are disabled.'])+
    box(390,85,320,180,'2 / Python Editor',['Open python.microbit.org','Load the complete .py file.','Connect with a data cable.'])+
    box(745,85,325,180,'3 / Transfer + run',['Send to micro:bit, or','download the .hex file and','copy it to MICROBIT.'])+
    '<text x="35" y="320" class="label">A .py file copied onto the USB drive is not a flashed program.</text><text x="35" y="355" class="note">Use MicroPython in the official Python Editor; do not paste this project into MakeCode Python.</text>',390)
svg('belief_math','One-dimensional belief: the same equations run on both computers',
    box(30,85,325,190,'PREDICT',['mu_minus = mu - speed*dt','                 - expected_coast','P_minus = P + Q','Use executed pulse duration.'])+
    box(390,85,320,190,'CORRECT',['K = P_minus / (P_minus + R)','mu = mu_minus','        + K*(reading - mu_minus)','P = max(floor, (1-K)*P_minus)'])+
    box(745,85,325,190,'INTERPRET',['mu: distance estimate (cm)','sqrt(P): model uncertainty','R: sensor noise variance','Q: movement uncertainty'])+
    '<text x="35" y="330" class="note">The variance floor is a conservative engineering heuristic. Repeated biased readings do not reveal the bias.</text>',370)
svg('decision','The robot moves only in short, explicit events',
    box(30,85,235,130,'OBSERVE',['Motors are stopped.','Read fresh distance.'])+arrow(270,150,295,150)+
    box(300,85,235,130,'UPDATE',['Check validity.','Update distance belief.'])+arrow(540,150,565,150)+
    box(570,85,235,130,'DECIDE',['MOVE / SAMPLE','DONE / ABORT'])+arrow(810,150,835,150)+
    box(840,85,230,130,'EXECUTE',['Pulse, then stop.','Wait for settling.'])+
    box(300,260,505,95,'If uncertainty remains',['Stay stopped; remeasure; terminate after bounded retries.'],fill='#fff3df')+
    '<path d="M955,220 L955,380 L145,380 L145,220" fill="none" stroke="#0D8080" stroke-width="3" marker-end="url(#arrow)"/>',410)
svg('calibration','Calibration makes symbols correspond to your robot',
    box(30,85,325,195,'SENSOR',['20 readings at each distance:','20, 30, 40 and 60 cm.','bias = mean(raw - true)','R = variance of residuals'])+
    box(390,85,320,195,'MOTION',['Repeat the same short pulse.','Measure powered travel','and coast after power-off.','Use at least five trials.'])+
    box(745,85,325,195,'CHECK',['Use fresh test distances.','Look for scale error or drift.','Verify stopping time.','Save floor and battery notes.'])+
    '<text x="35" y="335" class="note">If powered travel and coast cannot be separated, use a conservative total-pulse model and validate it.</text>',380)
svg('contexts','Same belief, different context: a deliberate pause',
    box(30,85,325,195,'SAME ESTIMATE',['Distance mean = 26 cm','Standard deviation = 2 cm','Predicted step = 1.11 cm','Extra margin = 0.5 cm'])+
    box(390,85,320,195,'NORMAL: k = 1.64',['26 - 1.64*2 - 1.11 - 0.5','= 21.11 cm','Above the lower band edge:','one short MOVE is allowed.'])+
    box(745,85,325,195,'CAREFUL: k = 2.33',['26 - 2.33*2 - 1.11 - 0.5','= 19.73 cm','Below the lower band edge:','remain stopped and SAMPLE.'],fill='#fff3df')+
    '<text x="35" y="335" class="note">Illustrative initial conditions matching the unit test. Neither mode guarantees safety under an incorrect model.</text>',380)
svg('roadmap','Build capability one verified step at a time',
    box(30,85,235,200,'SESSION 1',['Buy / assemble','Flash sensor program','Read distances','No motor motion'])+
    box(300,85,235,200,'SESSION 2',['Supported wheels','One short pulse','Calibrate sensing','Calibrate motion'])+
    box(570,85,235,200,'SESSION 3',['Raw baseline','Belief controller','Mini normal/careful','Measure real outcomes'])+
    box(840,85,230,200,'SESSION 4',['Repeat trials','Compare failures','Plot measurements','Write your conclusion'])+
    '<text x="35" y="340" class="note">Planning estimate: 12–20 learning hours after delivery, depending on programming and calibration experience.</text>',380)

items=[
('Kitronik :MOVE Motor 5683',1,44.38,'observed listing incl. VAT','RS Germany','https://de.rs-online.com/web/p/bbc-micro-bit-add-ons/2048249','Core; includes chassis/motors/sensor/AA holders'),
('BBC micro:bit V2.21 Go Bundle',1,18.90,'observed listing incl. VAT','BerryBase','https://www.berrybase.de/bbc-micro-bit-v2.21-go-bundle','Core; USB data cable included'),
('Four matched alkaline AA cells',1,5.00,'planning allowance','dm local / batteries category','https://www.dm.de/haushalt/batterien-und-akkus','Use AA, not bundle AAA; local pickup avoids postage'),
('Ruler or tape measure',1,5.00,'planning allowance','Local stationery / hardware shop','','Reuse existing if available'),
('Removable floor tape',1,4.00,'planning allowance','Local stationery / hardware shop','','For start marks, not a line-following requirement'),
('Broad cardboard target',1,0.00,'reuse assumption','Reuse a packaging box','','Stable, flat and perpendicular to sensor'),
('Laptop and USB data cable',1,0.00,'existing laptop + included cable','Existing equipment','','Optional USB-C cable if needed; not included in base'),
('Delivery across suppliers',1,15.00,'planning allowance','Checkout-specific','','Replace with actual combined delivery costs'),
('Price and replacement reserve',1,15.00,'planning allowance','Retained budget','','Unused funds are not spending'),
]
with (R/'shopping_list.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['item','quantity','unit_eur','price_status','seller','url','notes']);w.writerows(items)
total=round(sum(q*p for _,q,p,*_ in items),2)
budget={'checked_date':'2026-09-09','currency':'EUR','planning_total':total,'core_listed_hardware':63.28,'delivery_allowance':15,'reserve':15,'not_a_checkout_quote':True,
        'alternate_chassis':{'seller':'DigiKey Germany','listed_incl_vat_eur':39.08,'url':'https://www.digikey.de/de/products/detail/kitronik-ltd/5683/12525204','status':'search listing; checkout price and delivery unverified'},
        'optional_usb_c_cable':{'allowance_eur':6,'url':'https://www.berrybase.de/usb-2.0-adapterkabel-usb-c-stecker-micro-b-stecker-schwarz/laenge-1-0-m'},
        'phases':[{'phase':'Simulation','eur':0},{'phase':'Hardware + consumables','eur':77.28},{'phase':'Delivery','eur':15},{'phase':'Retained reserve','eur':15}]}
(R/'budget.json').write_text(json.dumps(budget,indent=2))
print('Created 10 SVG diagrams; planning total EUR',total)
