"""Reproducible publisher CSV ingestion. Raw archive remains unchanged."""
from pathlib import Path
import hashlib, json, sqlite3, zipfile, datetime
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
raw=ROOT/'data/raw/olist.zip'
out=ROOT/'data/processed'; out.mkdir(parents=True,exist_ok=True)
names=['orders','order_items','order_payments','order_reviews','products','customers','sellers']
manifest={'publisher':'Olist','url':'https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce','license':'CC BY-NC-SA 4.0','downloaded':datetime.datetime.now(datetime.timezone.utc).date().isoformat(),'archive_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'files':{},'source':'REAL_PUBLIC','currency':'BRL','excluded':'geolocation; no operational stock inferred'}
with zipfile.ZipFile(raw) as z, sqlite3.connect(out/'olist.sqlite') as c:
    for name in names+['product_category_name_translation']:
        file=(f'olist_{name}_dataset.csv' if name in names else f'{name}.csv')
        content=z.read(file)
        from io import BytesIO
        df=pd.read_csv(BytesIO(content))
        if name=='orders' and df.order_id.duplicated().any(): raise ValueError('Duplicate order IDs')
        if name=='order_items' and df.duplicated(['order_id','order_item_id']).any(): raise ValueError('Duplicate item keys')
        df.to_sql(name,c,if_exists='replace',index=False)
        manifest['files'][file]={'sha256':hashlib.sha256(content).hexdigest(),'rows':len(df),'columns':list(df.columns)}
    c.executescript('''
    CREATE INDEX IF NOT EXISTS ix_order_id ON orders(order_id);
    CREATE INDEX IF NOT EXISTS ix_items_order ON order_items(order_id);
    CREATE INDEX IF NOT EXISTS ix_items_product ON order_items(product_id);
    CREATE INDEX IF NOT EXISTS ix_products ON products(product_id);
    CREATE INDEX IF NOT EXISTS ix_reviews_order ON order_reviews(order_id);
    DROP VIEW IF EXISTS sales_lines;
    CREATE VIEW sales_lines AS SELECT o.order_id,o.order_purchase_timestamp AS purchased,o.order_status,o.order_delivered_customer_date,o.order_estimated_delivery_date,i.order_item_id,i.product_id,i.seller_id,CAST(ROUND(i.price*100) AS INTEGER) AS price_cents,CAST(ROUND(i.freight_value*100) AS INTEGER) AS freight_cents,COALESCE(t.product_category_name_english,p.product_category_name,'unknown') AS category FROM orders o JOIN order_items i USING(order_id) LEFT JOIN products p USING(product_id) LEFT JOIN product_category_name_translation t USING(product_category_name);
    ''')
    orphan=c.execute('SELECT COUNT(*) FROM order_items i LEFT JOIN orders o USING(order_id) WHERE o.order_id IS NULL').fetchone()[0]
    assert orphan==0
    manifest['coverage']=c.execute('SELECT MIN(order_purchase_timestamp),MAX(order_purchase_timestamp),COUNT(*) FROM orders').fetchone()
    manifest['checks']={'orphan_order_items':orphan,'item_price_cents':c.execute('SELECT SUM(CAST(ROUND(price*100) AS INTEGER)) FROM order_items').fetchone()[0],'sales_view_price_cents':c.execute('SELECT SUM(price_cents) FROM sales_lines').fetchone()[0]}
    assert manifest['checks']['item_price_cents']==manifest['checks']['sales_view_price_cents']
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'coverage':manifest['coverage'],'checks':manifest['checks'],'tables':{k:v['rows'] for k,v in manifest['files'].items()}},indent=2))
