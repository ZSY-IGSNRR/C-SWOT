# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Shengyu Zou and the contributors identified in AUTHORS.md.
"""Public inference core: satellite inputs and frozen parameters only.

No fitting, measured-discharge input, or outcome-based quality screening.
The formulas preserve the native v15 Manning/area/width calculation.
"""
import numpy as np

EPS, WIDTH_FLOOR, AREA_FLOOR = 1e-12, 1e-6, 1e-8


def apply_model(model, wse, slope):
    h, s = np.asarray(wse, float), np.asarray(slope, float)
    x, y = np.asarray(model['curve_wse'], float), np.asarray(model['curve_width'], float)
    if not (len(x) == len(y) > 0 and np.all(np.diff(x) > 0) and np.isfinite(y).all() and (y > 0).all()):
        raise ValueError('Invalid frozen geometry')
    width = np.maximum(np.interp(h, x, y), WIDTH_FLOOR)
    fallback = float(model['train_slope_fallback'])
    if not np.isfinite(fallback) or fallback <= 0:
        raise ValueError('Saved positive slope reference is required')
    slope_used = np.maximum(np.where(np.isfinite(s) & (s > 0), s, fallback), EPS)
    bed_h, bed_w = float(model['WSE0']), max(float(model['width0']), 0.)
    beta = max(float(model['beta']), EPS)
    a0 = .5 * (bed_w + y[0]) * max(x[0] - bed_h, 0.)
    area = np.full(len(h), np.nan)
    position = np.full(len(h), 'invalid', dtype=object)
    for i, (ht, wt) in enumerate(zip(h, width)):
        if not np.isfinite(ht):
            continue
        if ht <= bed_h:
            area[i], position[i] = AREA_FLOOR, 'below_wse0'
        elif ht < x[0]:
            area[i] = max(.5 * (bed_w + wt) * (ht - bed_h), AREA_FLOOR)
            position[i] = 'below_train_min_wse'
        else:
            inside = (x > x[0]) & (x < ht)
            xx = np.concatenate([[x[0]], x[inside], [ht]])
            yy = np.concatenate([[y[0]], y[inside], [wt]])
            delta = float(np.sum(np.maximum(np.diff(xx), 0.) * (yy[:-1] + yy[1:]) / 2.)) if ht > x[0] else 0.
            area[i] = max(a0 + beta * delta, AREA_FLOOR)
            position[i] = 'above_train_max_wse' if ht > x[-1] else 'within_train_wse_range'
    q = (1. / max(float(model['n']), EPS)) * area ** (5. / 3.) * width ** (-2. / 3.) * np.sqrt(slope_used)
    return {'Q_estimated': q, 'width_used': width, 'slope_used': slope_used,
            'area': area, 'area_position': position,
            'slope_was_repaired': ~(np.isfinite(s) & (s > 0))}


if __name__ == '__main__':
    import argparse, json
    import pandas as pd
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Reproduce estimates from a public variant table and its frozen model files.')
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--models', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output exists; choose a new file.')
    frame = pd.read_csv(args.input, usecols=['station_id', 'row_id', 'WSE', 'slope_observed'], dtype={'station_id': str})
    frame['Q_reproduced'] = np.nan
    for sid, group in frame.groupby('station_id'):
        path = args.models / (sid + '.json')
        if path.exists():
            model = json.loads(path.read_text(encoding='utf-8'))
            frame.loc[group.index, 'Q_reproduced'] = apply_model(model, group.WSE, group.slope_observed)['Q_estimated']
    frame[['station_id', 'row_id', 'Q_reproduced']].to_csv(args.output, index=False)
