"""Optional USB recording while stationary or on supported wheels. Ctrl+C ends capture."""
import argparse,csv
from pathlib import Path
def main():
    p=argparse.ArgumentParser();p.add_argument('--port',required=True);p.add_argument('--out',default='data/usb_log.csv');a=p.parse_args()
    try: import serial
    except ImportError: raise SystemExit('Install pyserial: python -m pip install pyserial')
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    with serial.Serial(a.port,115200,timeout=1) as port,out.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['trial_id','time_ms','action','raw_cm','mu_cm','sd_cm','moves','reason'])
        try:
            while True:
                line=port.readline().decode('utf-8',errors='replace').strip()
                if line: print(line)
                if line.startswith('LOG,'):
                    values=line.split(',')[1:]
                    if len(values)==8: w.writerow(values);f.flush()
        except KeyboardInterrupt: pass
if __name__=='__main__':main()
