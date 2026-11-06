"""Maintainer-specific check: DK1, N1-131 DataHub rows by date, hourly billing (mean of quarters)."""
import json, sys, datetime as dt, collections, math
D=sys.argv[1]
recs=json.load(open(D+'/dk1.json'))['records']
rows=[r for r in json.load(open(D+'/n1_CD.json'))['records'] if r['ChargeType']=='D03']
def grid(t):
    ds=t.strftime('%Y-%m-%d')
    for r in rows:
        if r['ValidFrom'][:10]<=ds and (r['ValidTo'] is None or r['ValidTo'][:10]>ds):
            v=r[f'Price{t.hour+1}']; return v if v is not None else r['Price1']
    raise KeyError(ds)
def flat(t): return (0.135+0.72) if t.year==2025 else (0.115+0.008)
# hourly mean spot per local hour start
q=collections.OrderedDict()
for r in recs:
    tl=dt.datetime.fromisoformat(r['TimeDK']); tu=dt.datetime.fromisoformat(r['TimeUTC'])
    key=tu.replace(minute=0)
    q.setdefault(key,[tl.replace(minute=0),[]])[1].append(r['DayAheadPriceDKK']/1000)
H=[(k,v[0],sum(v[1])/len(v[1])) for k,v in q.items() if len(v[1])==4]
spot={k:s for k,_,s in H}; loc={k:l for k,l,_ in H}
tot={k:(spot[k]+grid(loc[k])+flat(loc[k]))*1.25 for k in spot}
keys=sorted(spot)
def night_hours(day):  # local 17:00 day -> 07:00 next day, as UTC hour keys
    return [k for k in keys if (loc[k].date()==day and loc[k].hour>=17) or (loc[k].date()==day+dt.timedelta(days=1) and loc[k].hour<7)]
def cost_fill(hours, kwh, kw, rank=None):
    order=hours if rank is None else sorted(hours,key=rank)
    left=kwh; c=0
    for k in order:
        e=min(kw,left); c+=e*tot[k]; left-=e
        if left<=1e-9: break
    return c, left
def run(kwh, kw, d0, d1):
    res=collections.Counter(); n=0; pk=0; disagree=0
    day=d0
    while day<=d1:
        hs=night_hours(day)
        if len(hs)<13: day+=dt.timedelta(days=1); continue
        n+=1
        res['plug17']+=cost_fill(hs,kwh,kw)[0]
        res['timer00']+=cost_fill([k for k in hs if loc[k].hour<7 and loc[k].date()>day],kwh,kw)[0]
        res['smart_total']+=cost_fill(hs,kwh,kw,lambda k:(tot[k],-k.timestamp()))[0]
        res['smart_spot']+=cost_fill(hs,kwh,kw,lambda k:(spot[k],-k.timestamp()))[0]
        # plan at 11 kW, car delivers kw_real only: execute cheapest-first hours chosen for 11 kW, then re-plan remaining on what is left (receding)
        day+=dt.timedelta(days=1)
    return n,res
def underdelivery(kwh, kw_plan, kw_real, d0, d1):
    """Plan with kw_plan every hour (receding), car delivers kw_real; compare with planning at kw_real."""
    extra=0; n=0; short=0; day=d0
    while day<=d1:
        hs=night_hours(day)
        if len(hs)<13: day+=dt.timedelta(days=1); continue
        n+=1
        best=cost_fill(hs,kwh,kw_real,lambda k:(tot[k],-k.timestamp()))[0]
        left=kwh; c=0; deadline_slack=0
        for i,k in enumerate(hs):
            rem=hs[i:]
            need_hours=math.ceil(left/kw_plan-1e-9)
            chosen=sorted(rem,key=lambda x:(tot[x],-x.timestamp()))[:need_hours]
            if k in chosen and left>0:
                e=min(kw_real,left); c+=e*tot[k]; left-=e
        if left>1e-6: short+=1; c+=left*tot[hs[-1]]  # count shortfall as bought in last hour
        extra+=c-best; day+=dt.timedelta(days=1)
    return n,extra,short
import itertools
d0=dt.date(2026,1,1); d1=dt.date(2026,10,28)
for kwh,kw in [(6,11),(6,3.7),(15,11)]:
    n,r=run(kwh,kw,d0,d1); f=365/n
    print(f'{kwh} kWh @ {kw} kW, {n} nights 2026: '+', '.join(f'{k}={v*f:.0f}' for k,v in r.items()),
          f'| timer-plug17={(r["plug17"]-r["timer00"])*f:.0f} smart-vs-timer={(r["timer00"]-r["smart_total"])*f:.0f} spot-loss={(r["smart_spot"]-r["smart_total"])*f:.0f}')
for kwh,kp,kr in [(6,11,7.4),(6,11,3.7),(15,11,7.4),(15,11,3.7),(25,11,3.7)]:
    n,e,s=underdelivery(kwh,kp,kr,d0,d1); print(f'plan {kp} kW, real {kr} kW, {kwh} kWh: extra {e*365/n:.0f} DKK/yr, nights short {s}/{n}')
