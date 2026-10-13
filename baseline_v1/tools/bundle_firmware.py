"""Create single-file MicroPython programs for drag/drop into the official editor."""
from pathlib import Path
import re,hashlib,json
R=Path(__file__).resolve().parents[1];F=R/'firmware';O=R/'flash';O.mkdir(exist_ok=True)
vendor=(F/'KitronikMOVEMotor.py').read_text(encoding='utf-8').replace('\r','')
vendor=re.sub(r'\n{3,}','\n\n',vendor)
controller=(F/'belief_controller.py').read_text()
hw=(F/'hardware.py').read_text().replace('from KitronikMOVEMotor import MOVEMotor','')
main=(F/'main.py').read_text().replace('import config as C','').replace('from hardware import Robot','').replace('from belief_controller import Controller','')
base=(F/'config.py').read_text()
names=[('01_sensor_only','sensor','mini','normal'),('02_supported_wheel_test','motor_test','mini','normal'),
       ('03_pulse_calibration','pulse_calibration','mini','normal'),('04_raw_baseline','run','raw','normal'),
       ('05_belief_baseline','run','belief','normal'),('06_mini_normal','run','mini','normal'),('07_mini_careful','run','mini','careful')]
manifest={}
for name,mode,policy,context in names:
    config=base.replace("MODE = 'sensor'","MODE = '%s'"%mode).replace("POLICY = 'mini'","POLICY = '%s'"%policy).replace("CONTEXT = 'normal'","CONTEXT = '%s'"%context)
    config='class C:\n'+'\n'.join('    '+line for line in config.splitlines())+'\n'
    text='# Mini-IPHOREOS: '+name+'\n# Generated from firmware/. All motor enables remain False until you edit them.\n'+config+'\n'+vendor+'\n'+controller+'\n'+hw+'\n'+main
    compile(text,name,'exec')
    p=O/(name+'.py');p.write_text(text,encoding='utf-8')
    manifest[p.name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(O/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('Built',len(names),'single-file programs; no hardware was flashed.')
