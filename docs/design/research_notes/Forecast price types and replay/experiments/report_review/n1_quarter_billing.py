import json,sys,datetime as dt
D=sys.argv[1]
recs=json.load(open(D+'/dk1.json'))['records']
rows=[r for r in json.load(open(D+'/n1_CD.json'))['records'] if r['ChargeType']=='D03']
def grid(t,hard):
    if hard:
        w=t.month>=10 or t.month<=3; lo,hi,pk=(0.088,0.264,0.791) if w else (0.088,0.132,0.343)
        return lo if t.hour<6 else pk if 17<=t.hour<21 else hi
    ds=t.strftime('%Y-%m-%d')
    for r in rows:
        if r['ValidFrom'][:10]<=ds and (r['ValidTo'] is None or r['ValidTo'][:10]>ds):
            v=r[f'Price{t.hour+1}']; return v if v is not None else r['Price1']
Q=[(dt.datetime.fromisoformat(r['TimeDK']),r['DayAheadPriceDKK']/1000) for r in recs]
for hard in (True,False):
  for d0,d1 in [(dt.date(2026,1,1),dt.date(2026,10,28))]:
    res={'plug17':0,'timer00':0,'smart':0,'spot':0};n=0;day=d0
    while day<=d1:
        qs=[(t,s,(s+grid(t,hard)+0.123)*1.25) for t,s in Q if (t.date()==day and t.hour>=17) or (t.date()==day+dt.timedelta(days=1) and t.hour<7)]
        if len(qs)<50: day+=dt.timedelta(days=1); continue
        n+=1
        def fill(order):
            left=6.0;c=0
            for t,s,tt in order:
                e=min(2.75,left);c+=e*tt;left-=e
                if left<=0:break
            return c
        res['plug17']+=fill(qs); res['timer00']+=fill([x for x in qs if x[0].date()>day])
        res['smart']+=fill(sorted(qs,key=lambda x:x[2])); res['spot']+=fill(sorted(qs,key=lambda x:x[1]))
        day+=dt.timedelta(days=1)
    print('hardcoded' if hard else 'datahub', n, {k:round(v) for k,v in res.items()}, 'scaled365', {k:round(v*365/n) for k,v in res.items()})
