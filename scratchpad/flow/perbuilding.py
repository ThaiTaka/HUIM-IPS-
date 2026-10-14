import sys, numpy as np, pandas as pd, json
sys.path.insert(0,'src')
import optimize_positioning as op
from preprocess_uji import fit_preprocessor, load_splits
from utils import *
tr,va=load_splits()
wap=[c for c in tr.columns if c.startswith('WAP')]
prep=fit_preprocessor(tr)
print('rssi bounds',prep.rssi_min_train,prep.rssi_max_train,len(tr),len(va))
W=tr[wap].to_numpy(float);C=tr[['LONGITUDE','LATITUDE']].to_numpy(float)
ybf=(tr.BUILDINGID.astype(str)+'_'+tr.FLOOR.astype(str)).to_numpy()
Wv=va[wap].to_numpy(float);Cv=va[['LONGITUDE','LATITUDE']].to_numpy(float)
op.GROUND=0.766126
cfg=op.Config('exponential','braycurtis',12,4.0,6,'positive')
ips=pd.read_csv('results/multi_dataset/uji/ips_results.csv')
r=ips[ips.condition=='huim_union__A_signal__1.9294pct'].iloc[0]
cols=[wap.index(w) for w in r.selected_waps.split(';')]
print('n86',len(cols))
rows=[]
for name,cc in [('S4_all520',None),('S4_huim86',cols)]:
    o=op.Positioner(W,C,ybf,cfg,cols=cc).predict(Wv)
    e=op.err_ground(o['xy'],Cv)
    pb=np.array([s.split('_')[0] for s in o['label']]).astype(int); pf=np.array([s.split('_')[1] for s in o['label']]).astype(int)
    d=pd.DataFrame({'b':va.BUILDINGID,'f':va.FLOOR,'e':e,'pb':pb,'pf':pf})
    d['bok']=d.b==d.pb; d['fok']=(d.b==d.pb)&(d.f==d.pf)
    d['cond']=name; rows.append(d)
    print(name,e.mean(),d.bok.mean(),d.fok.mean())
D=pd.concat(rows); D.to_csv('scratchpad/flow/perpred.csv',index=False)
for n,g in D.groupby('cond'):
    t=g.groupby('b').agg(n=('e','size'),mean=('e','mean'),med=('e','median'),p90=('e',lambda x:np.percentile(x,90)),mx=('e','max'),bacc=('bok','mean'),facc=('fok','mean'))
    print(n);print(t.round(4)); print('macro',t['mean'].mean())
