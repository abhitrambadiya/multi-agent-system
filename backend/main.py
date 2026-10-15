import asyncio,json,secrets,threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI,HTTPException,Request as HTTPRequest,Header
from fastapi.responses import StreamingResponse,JSONResponse,FileResponse
from fastapi.staticfiles import StaticFiles
from .config import Settings,ROOT
from .contracts import Request,Decision,PolicyEdit
from .engine import Engine


def create_app(settings=None,engine=None):
    settings=settings or Settings.env()
    @asynccontextmanager
    async def lifespan(app):
        app.state.engine=engine or Engine(settings)
        app.state.owner_token=secrets.token_urlsafe(32)
        app.state.worker=ThreadPoolExecutor(max_workers=1)
        app.state.busy=threading.Lock()
        # In-flight inference cannot be safely continued after a process crash.
        app.state.engine.store.execute("UPDATE workflows SET status='FAILED',error='Server restarted during computation; submit again.' WHERE status IN ('RUNNING','QUEUED')")
        yield
        app.state.worker.shutdown(wait=True)
        if not engine:app.state.engine.close()
    app=FastAPI(title='AI-EOS local research workforce',lifespan=lifespan)
    @app.middleware('http')
    async def local_boundary(request,call_next):
        host=request.headers.get('host','').split(':')[0]
        if host not in {'localhost','127.0.0.1','testserver'}:return JSONResponse({'detail':'Local host only'},403)
        origin=request.headers.get('origin')
        if origin and origin not in {'http://127.0.0.1:8010','http://localhost:8010','http://127.0.0.1:5173','http://localhost:5173'}:return JSONResponse({'detail':'Untrusted origin'},403)
        if request.method in {'POST','PUT','PATCH','DELETE'}:
            token=request.headers.get('x-owner-token','')
            if not secrets.compare_digest(token,getattr(request.app.state,'owner_token','invalid')):return JSONResponse({'detail':'Owner session required'},403)
        return await call_next(request)
    def eng():return app.state.engine
    def exclusive(fn):
        if not app.state.busy.acquire(blocking=False):raise HTTPException(409,'Another workflow is running; retry when it finishes.')
        try:return fn()
        finally:app.state.busy.release()
    @app.exception_handler(ValueError)
    async def invalid(_,exc):return JSONResponse({'detail':str(exc)},409)
    @app.exception_handler(LookupError)
    async def missing(_,exc):return JSONResponse({'detail':str(exc)},404)
    @app.get('/api/session')
    def session():return {'owner_token':app.state.owner_token,'scope':'LOCAL_SINGLE_OWNER_SIMULATION'}
    @app.get('/api/health')
    def health():return {'status':'ok','mode':settings.mode,'model':eng().llm.health(),'embedding':eng().embedding_mode,'dataset':eng().analytics.manifest(),'financial_execution':'SIMULATED_ONLY'}
    @app.get('/api/workflows')
    def workflows():return eng().store.rows('SELECT id,request,status,created,error FROM workflows ORDER BY created DESC LIMIT 30')
    @app.post('/api/workflows',status_code=202)
    def start(request:Request):
        if not app.state.busy.acquire(blocking=False):raise HTTPException(409,'Another workflow is running.')
        try:wid=eng().start(request)
        except Exception:
            app.state.busy.release();raise
        def run():
            try:eng().run(wid)
            finally:app.state.busy.release()
        app.state.worker.submit(run)
        return {'id':wid,'status':'QUEUED'}
    @app.get('/api/workflows/{wid}')
    def workflow(wid:str):return eng().get(wid)
    @app.get('/api/workflows/{wid}/events')
    async def events(wid:str,request:HTTPRequest,after:int=0,last_event_id:str|None=Header(None)):
        eng().get(wid)
        try:cursor=max(after,int(last_event_id or 0))
        except ValueError:raise HTTPException(422,'Invalid event cursor')
        async def stream():
            nonlocal cursor
            while not await request.is_disconnected():
                rows=eng().store.rows('SELECT * FROM events WHERE workflow_id=? AND seq>? ORDER BY seq',(wid,cursor))
                for row in rows:
                    cursor=row['seq'];row['payload']=json.loads(row['payload'])
                    yield f"id: {cursor}\ndata: {json.dumps(row)}\n\n"
                state=eng().store.one('SELECT status FROM workflows WHERE id=?',(wid,))['status']
                if state in {'COMPLETED','FAILED','CANCELLED','AWAITING_APPROVAL'}:
                    yield 'event: settled\ndata: {}\n\n';break
                yield ': heartbeat\n\n'
                await asyncio.sleep(.4)
        return StreamingResponse(stream(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})
    @app.post('/api/actions/{aid}/decision')
    def decision(aid:str,body:Decision):return exclusive(lambda:eng().decide(aid,body.decision,body.digest))
    @app.post('/api/purchase-orders/{po}/receive')
    def receive(po:str):return exclusive(lambda:eng().store.receive(po))
    @app.get('/api/business/metrics')
    def metrics(category:str='furniture_decor',period_a:str='2018-05',period_b:str='2018-06'):return {'historical':eng().analytics.compare(category,period_a,period_b),'operations':eng().store.operations(),'categories':eng().analytics.categories()}
    @app.get('/api/evidence/{eid}')
    def evidence(eid:str):
        row=eng().store.one('SELECT * FROM evidence WHERE id=?',(eid,))
        if not row:raise LookupError('Evidence not found')
        return row
    @app.post('/api/demo/policy')
    def policy(body:PolicyEdit):return exclusive(lambda:(eng().store.update_policy(body.days) or eng().store.operations()))
    @app.post('/api/demo/reset')
    def reset(workspace:str):
        if workspace!='local-demo':raise ValueError('Only local-demo can be reset')
        return exclusive(lambda:(eng().store.reset() or {'status':'reset','workspace':workspace}))
    @app.get('/api/research')
    def research():
        result_path=ROOT/'results/benchmark/summary.json'
        return {'summary':json.loads(result_path.read_text()) if result_path.exists() else None,'invocations':eng().store.rows('SELECT * FROM invocations ORDER BY created DESC LIMIT 100'),'cache_entries':eng().store.one('SELECT COUNT(*) AS count FROM cache')['count'],'threshold':settings.threshold}
    @app.get('/api/experiments/{experiment_id}')
    def experiment(experiment_id:str):
        if experiment_id!='benchmark':raise LookupError('Experiment not found')
        path=ROOT/'results/benchmark/summary.json'
        if not path.exists():raise LookupError('Benchmark has not run')
        return json.loads(path.read_text())
    dist=ROOT/'frontend/dist'
    if dist.exists():
        app.mount('/assets',StaticFiles(directory=dist/'assets'),name='assets')
        @app.get('/')
        def index():return FileResponse(dist/'index.html')
    return app

app=create_app()
