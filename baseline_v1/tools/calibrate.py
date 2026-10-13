"""Summarise YOUR measured CSVs; never silently activates motors or edits config."""
from pathlib import Path
import argparse,csv,json,statistics as st
def rows(path):
    with open(path,newline='',encoding='utf-8-sig') as f: return list(csv.DictReader(f))
def main():
    p=argparse.ArgumentParser();p.add_argument('--sensor',required=True);p.add_argument('--motion');p.add_argument('--out',default='results/my_calibration.json');a=p.parse_args()
    sr=rows(a.sensor);errors=[float(r['raw_cm'])-float(r['true_cm']) for r in sr]
    if len(errors)<10: raise ValueError('Collect at least 10 readings; guide recommends 20 at each of four distances.')
    result={'sensor_n':len(errors),'sensor_bias_cm':st.mean(errors),'measurement_var':max(.1,st.variance(errors)),
            'note':'Check distance-dependent bias, correlation and held-out errors before applying these summaries. Variance floor and margins still need judgement.'}
    if a.motion:
        mr=rows(a.motion)
        if len(mr)<5: raise ValueError('Collect at least five repeated pulse trials')
        speeds=[float(r['powered_distance_cm'])/float(r['powered_time_s']) for r in mr]
        coasts=[float(r['coast_cm']) for r in mr]
        result.update(speed_cm_s=st.mean(speeds),coast_cm=st.mean(coasts),max_observed_coast_cm=max(coasts),motion_trials=len(mr),
                      motion_var=st.variance([float(r['powered_distance_cm'])+float(r['coast_cm']) for r in mr]))
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
