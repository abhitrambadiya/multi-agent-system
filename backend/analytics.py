import json, sqlite3, re
from pathlib import Path
from .db import digest

class Analytics:
    def __init__(self,path): self.path=Path(path)
    def query(self,sql,args=()):
        if not self.path.exists(): raise ValueError('Olist data missing: run scripts/ingest.py')
        with sqlite3.connect(f'file:{self.path}?mode=ro',uri=True) as c:
            c.row_factory=sqlite3.Row
            return [dict(r) for r in c.execute(sql,args)]
    def manifest(self):
        path=self.path.parent/'manifest.json'
        return json.loads(path.read_text()) if path.exists() else {'source':'MISSING','archive_sha256':'missing'}
    def categories(self): return self.query("SELECT category,COUNT(*) AS items FROM sales_lines WHERE order_status='delivered' GROUP BY category ORDER BY items DESC LIMIT 30")
    def compare(self,category,period_a,period_b):
        for p in [period_a,period_b]:
            if not re.fullmatch(r'201[67]-\d{2}|2018-0[1-7]',p) or not 1<=int(p[-2:])<=12: raise ValueError('Choose a complete historical month (2017 or Jan-Jul 2018)')
            if p < '2017-01': raise ValueError('Boundary data: choose 2017 or Jan-Jul 2018')
        if category not in [r['category'] for r in self.categories()]: raise ValueError('Choose a supported category')
        # Each item counted once. Payments/reviews never join this aggregate.
        periods=[]
        for p in [period_a,period_b]:
            r=self.query("SELECT COUNT(DISTINCT order_id) AS orders,COUNT(*) AS items,COALESCE(SUM(price_cents),0) AS sales_cents,COALESCE(SUM(freight_cents),0) AS freight_cents FROM sales_lines WHERE category=? AND substr(purchased,1,7)=? AND order_status='delivered'",(category,p))[0]
            r['period']=p
            periods.append(r)
        a,b=periods
        return {'source':'REAL_PUBLIC','currency':'BRL','category':category,'periods':periods,'delta_cents':b['sales_cents']-a['sales_cents'],'delta_pct':round(100*(b['sales_cents']-a['sales_cents'])/a['sales_cents'],2) if a['sales_cents'] else None,'definition':'Delivered orders; product sales exclude freight. Item rows counted once. Period is purchase month. Historical association does not prove cause.'}
    def reviews(self,category,limit=120):
        return self.query('''SELECT r.review_id,r.order_id,r.review_score,r.review_comment_message AS text FROM order_reviews r WHERE r.review_comment_message IS NOT NULL AND length(r.review_comment_message)>15 AND EXISTS(SELECT 1 FROM sales_lines s WHERE s.order_id=r.order_id AND s.category=?) ORDER BY r.review_creation_date,r.review_id LIMIT ?''',(category,limit))
