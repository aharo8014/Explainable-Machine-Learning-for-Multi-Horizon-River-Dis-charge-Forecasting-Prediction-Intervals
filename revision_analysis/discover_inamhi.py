from pathlib import Path
import json, re, requests, fitz, pandas as pd

OUT=Path('revision_outputs'); OUT.mkdir(exist_ok=True)
PDFS={y:f'https://www.inamhi.gob.ec/wp-content/uploads/downloads/2013/12/Ah-{y}.pdf' for y in [1990,1991,1992,1993]}
coords=[(-1.80217,-79.53443),(-1.83547,-79.44170)]

def get(url,path):
 r=requests.get(url,timeout=180,headers={'User-Agent':'Mozilla/5.0'}); r.raise_for_status(); path.write_bytes(r.content); return r

manifest=[]
for y,u in PDFS.items():
 p=OUT/f'INAMHI_AH_{y}.pdf'
 try:
  r=get(u,p); doc=fitz.open(p); hits=[]
  for i,page in enumerate(doc):
   t=page.get_text('text')
   if re.search(r'H\s*0?371|SAN\s+PABLO|PALMAR',t,re.I):
    hits.append({'page':i+1,'text':t[:8000]})
    pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
    pix.save(OUT/f'INAMHI_{y}_page_{i+1}.png')
  (OUT/f'INAMHI_{y}_hits.json').write_text(json.dumps(hits,ensure_ascii=False,indent=2),encoding='utf-8')
  manifest.append({'year':y,'url':u,'status':'ok','bytes':len(r.content),'pages':len(doc),'hits':[h['page'] for h in hits]})
 except Exception as e: manifest.append({'year':y,'url':u,'status':'error','error':repr(e)})

for lat,lon in coords:
 for y in [1990,1991,1992,1993,2012,2017,2025]:
  url='https://flood-api.open-meteo.com/v1/flood'
  params={'latitude':lat,'longitude':lon,'start_date':f'{y}-01-01','end_date':f'{y}-12-31','daily':'river_discharge','timezone':'America/Guayaquil'}
  try:
   r=requests.get(url,params=params,timeout=180); r.raise_for_status(); js=r.json(); d=js['daily']
   pd.DataFrame({'date':d['time'],'river_discharge':d['river_discharge']}).to_csv(OUT/f'glofas_{lat}_{lon}_{y}.csv',index=False)
   manifest.append({'year':y,'lat':lat,'lon':lon,'status':'api_ok','url':r.url})
  except Exception as e: manifest.append({'year':y,'lat':lat,'lon':lon,'status':'api_error','error':repr(e)})

(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))