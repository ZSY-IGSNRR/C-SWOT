# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Shengyu Zou and the contributors identified in AUTHORS.md.
"""Reproduce both released QC variants from the public archive and models."""
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from frozen_model import apply_model


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package',type=Path,default=Path(__file__).resolve().parent.parent)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():p.error('Output exists; choose a new directory.')
    original=pd.read_csv(a.package/'data/retained/all_observations.csv',dtype={'station_id':str})
    # Strict acceptance is independent of discharge estimates and labels.
    eligible=original.source_qc_complete & ~original[['overall_bad','wse_hampel','width_hampel','slope_hampel']].any(axis=1)
    models={f.stem:json.loads(f.read_text(encoding='utf-8')) for f in (a.package/'models').glob('*.json')}
    a.output.mkdir(parents=True)
    result={}
    for variant,frame in [('strict',original.loc[eligible].copy()),('retained',original.copy())]:
        # No excluded row is included in a strict model call.
        frame['Q_estimated']=np.nan
        for sid,part in frame.groupby('station_id'):
            if sid in models:
                predicted=apply_model(models[sid],part.WSE,part.slope_observed)
                for k in ['Q_estimated','width_used','slope_used','area','area_position','slope_was_repaired']:
                    frame.loc[part.index,k]=predicted[k]
        frame.to_csv(a.output/(variant+'_observations.csv'),index=False)
        result[variant]={'records':len(frame),'computed':int(frame.Q_estimated.notna().sum())}
    excluded=original.loc[~eligible,['station_id','row_id','source_row_id','datetime','WSE','width_observed','slope_observed','source_qc_complete','overall_bad','wse_hampel','width_hampel','slope_hampel']]
    excluded.to_csv(a.output/'strict_excluded_satellite_records.csv',index=False)
    result['excluded_records']=len(excluded)
    (a.output/'reproduction_summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
