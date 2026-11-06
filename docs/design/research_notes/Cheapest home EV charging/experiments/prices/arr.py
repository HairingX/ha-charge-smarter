import runpy,io,contextlib,json,collections
buf=io.StringIO()
with contextlib.redirect_stdout(buf): g=runpy.run_path('analyse.py')
total=g['total'];D=g['D']
for area in ['DK1','DK2']:
    q=[(x['TimeDK'],x['DayAheadPriceDKK']/1000) for x in json.load(open(D+'dap_%s.json'%area))['records']]
    tq=[total(area,t,p) for t,p in q]; idx={t:i for i,(t,p) in enumerate(q)}
    kwh,kw=6.0,11.0; nq=kwh/(kw/4); nf=int(nq); fr=nq-nf
    res=collections.defaultdict(float); n=0
    for d in sorted({t[:10] for t,p in q if "2026-01-01"<=t<"2026-10-29"}):
        i0=idx.get(d+'T17:00:00')
        if i0 is None or i0+56>len(q): continue
        n+=1; win=list(range(i0,i0+56))
        c=lambda o:(sum(tq[i] for i in o[:nf])+fr*tq[o[nf]])*kw/4
        for arr in (17,19,22):
            w=win[(arr-17)*4:]
            res['dumb%d'%arr]+=c(w)
        res['smart']+=c(sorted(win,key=lambda i:tq[i]))
        # cheapest within 00-06 only, (simple "night tariff" timer)
        res['timer00']+=c(win[28:])
    print(area,{k:round(v*365/n) for k,v in res.items()},'nights',n)
