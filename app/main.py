from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
import hashlib
import io
import json
import secrets
import time
import uuid
import zipfile

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from .accounts import Directory, LOCKOUT_SECONDS
from .config import Settings, is_loopback_origin
from .capabilities import BUILD_VERSION, manifest
from .engine import analyze, public_result
from .qr import decode_image, MAX_IMAGE_BYTES
from .schemas import (ScanRequest, ReportRequest, ReviewRequest, LoginRequest,
                      MfaRequest, StaffStatusRequest)
from .storage import Store, DEFAULT_ORG_ID

class BodyLimit:
    """Cap untrusted bytes before the framework buffers a request body."""
    def __init__(self, app): self.app=app
    async def __call__(self, scope, receive, send):
        if scope['type']!='http' or scope['method'] not in {'POST','PUT','PATCH'}:
            return await self.app(scope,receive,send)
        limit=MAX_IMAGE_BYTES if scope['path']=='/api/qr/decode' else 32768
        body=bytearray()
        while True:
            message=await receive()
            if message['type']=='http.disconnect': return
            body.extend(message.get('body',b''))
            if len(body)>limit:
                return await JSONResponse({'detail':'Request is too large.'},status_code=413)(scope,receive,send)
            if not message.get('more_body'): break
        sent=False
        async def replay():
            nonlocal sent
            if not sent:
                sent=True
                return {'type':'http.request','body':bytes(body),'more_body':False}
            return await receive()
        await self.app(scope,replay,send)

@dataclass
class Scan:
    data: dict
    token_hash: str
    expiry: float

class TransientScans:
    def __init__(self, ttl, capacity):
        self.ttl,self.capacity,self.data,self.lock=ttl,capacity,{},Lock()
    def add(self,result):
        with self.lock:
            self.data={k:v for k,v in self.data.items() if v.expiry>time.time()}
            if len(self.data)>=self.capacity:
                raise HTTPException(503,'Local check capacity reached; retry later.')
            id_,token=uuid.uuid4().hex,secrets.token_urlsafe(32)
            self.data[id_]=Scan(result,hashlib.sha256(token.encode()).hexdigest(),time.time()+self.ttl)
            return id_,token
    def get(self,id_,token):
        with self.lock:
            record=self.data.get(id_)
            if record and record.expiry<=time.time():
                self.data.pop(id_,None)
                record=None
            if not record or not secrets.compare_digest(record.token_hash,hashlib.sha256(token.encode()).hexdigest()):
                raise HTTPException(404,'Check not found, expired, or access denied.')
            return record.data
    def delete(self,id_,token):
        self.get(id_,token)
        with self.lock: self.data.pop(id_,None)

class Limiter:
    def __init__(self,limit): self.limit,self.items,self.lock=limit,defaultdict(deque),Lock()
    def allow(self,key):
        now=time.monotonic()
        with self.lock:
            # Local memory guard; production needs edge + distributed throttling.
            if len(self.items)>5000:
                self.items=defaultdict(deque,{k:v for k,v in self.items.items() if v and v[-1]>now-60})
                if len(self.items)>5000: return False
            bucket=self.items[key]
            while bucket and bucket[0]<now-60: bucket.popleft()
            if len(bucket)>=self.limit: return False
            bucket.append(now)
            return True

def bearer(value):
    return value[7:] if value and value.startswith('Bearer ') else ''

def create_app(settings: Settings | None = None):
    settings=settings or Settings.from_env()
    store=Store(settings.database,settings.report_ttl_days)
    directory=Directory(store)
    scans=TransientScans(settings.scan_ttl_seconds,settings.max_scans)
    limiter=Limiter(settings.rate_limit)
    app=FastAPI(title='Trust.kh local prototype',version=BUILD_VERSION,docs_url=None,redoc_url=None,openapi_url='/api/openapi.json')
    app.state.store,app.state.scans,app.state.directory=store,scans,directory
    app.add_middleware(BodyLimit)

    @app.middleware('http')
    async def security(request:Request,call_next):
        origin=request.headers.get('origin')
        # Enforce Origin only on state-changing requests, which is all a CSRF-style
        # control protects. Module scripts and webfonts are fetched in CORS mode and
        # send Origin even same-origin, so checking it on GET meant one wrong
        # TRUST_ORIGIN returned 403 for /app.js and the fonts — the stylesheet still
        # loaded, so the page looked correct while the entire application was inert.
        # A misconfigured deployment must fail loudly, not silently.
        unsafe=request.method in {'POST','PUT','PATCH','DELETE'}
        if unsafe and origin and origin not in set(settings.allowed_origins) and not is_loopback_origin(origin):
            response=JSONResponse({'detail':'Origin is not allowed for this request.'},status_code=403)
        elif request.url.path.startswith('/api/') and not limiter.allow(hashlib.sha256((settings.hmac_key+(request.client.host if request.client else 'unknown')).encode()).hexdigest()):
            response=JSONResponse({'detail':'Too many requests. Retry in one minute.'},status_code=429,headers={'Retry-After':'60'})
        else:
            response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Permissions-Policy']='camera=(),microphone=(),geolocation=()'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob: data:; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        if settings.demo:
            # The demo is served over TLS by the host; do not let it be downgraded.
            response.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control']='no-store'
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Do not echo untrusted inputs / secrets in validation errors or logs.
        return JSONResponse({'detail':'Invalid request fields, consent, or input length.'},status_code=422)

    def require(authorization, capability):
        """Every protected route resolves a named principal, then checks one capability."""
        principal=directory.principal(bearer(authorization))
        if principal is None:
            raise HTTPException(401,'Sign in with a named staff account.')
        if not principal.mfa_satisfied:
            raise HTTPException(403,'Complete the second factor before continuing.')
        if not principal.can(capability):
            raise HTTPException(403,'Your role does not include this action.')
        return principal

    @app.post('/api/auth/login')
    def login(request:LoginRequest):
        result=directory.authenticate(request.email,request.password)
        if 'session' in result:
            return result
        if result.get('error')=='locked':
            raise HTTPException(429,'Too many failed attempts. This account is temporarily locked.',
                                headers={'Retry-After':str(result.get('retry_after',LOCKOUT_SECONDS))})
        # Identical response for unknown email and wrong password.
        raise HTTPException(401,'Email or password is incorrect.')

    @app.post('/api/auth/mfa')
    def submit_mfa(request:MfaRequest,authorization:str|None=Header(default=None)):
        if not directory.submit_mfa(bearer(authorization),request.code):
            raise HTTPException(401,'That code is not valid. Check your authenticator app.')
        principal=directory.principal(bearer(authorization))
        return {'authenticated':True,'role':principal.role,'organization':principal.org_id,
                'display_name':principal.display_name}

    @app.get('/api/auth/me')
    def whoami(authorization:str|None=Header(default=None)):
        principal=directory.principal(bearer(authorization))
        if principal is None:
            raise HTTPException(401,'No active session.')
        return {'email':principal.email,'display_name':principal.display_name,'role':principal.role,
                'organization':principal.org_id,'mfa_satisfied':principal.mfa_satisfied}

    @app.post('/api/auth/logout',status_code=204)
    def logout(authorization:str|None=Header(default=None)):
        directory.end_session(bearer(authorization))
        return Response(status_code=204)

    @app.get('/api/capabilities')
    def capabilities():
        return manifest(demo=settings.demo)

    @app.get('/api/health')
    def health():
        return {'status':'ok','mode':'public_demo' if settings.demo else 'local_starter',
                'report_intake':not settings.demo,'live_reputation':False,'external_requests':False}

    @app.post('/api/scans',status_code=201)
    def scan(request:ScanRequest):
        try: result=analyze(request.kind,request.text,settings.hmac_key)
        except ValueError as exc: raise HTTPException(422,str(exc)) from exc
        # Raw message text is intentionally discarded, not put into the scan store.
        id_,token=scans.add(result)
        return {'scan_id':id_,'access_token':token,'expires_in':settings.scan_ttl_seconds,**public_result(result)}

    @app.get('/api/scans/{id_}')
    def get_scan(id_:str,authorization:str|None=Header(default=None)):
        return public_result(scans.get(id_,bearer(authorization)))

    @app.delete('/api/scans/{id_}',status_code=204)
    def forget_scan(id_:str,authorization:str|None=Header(default=None)):
        scans.delete(id_,bearer(authorization))
        return Response(status_code=204)

    @app.post('/api/qr/decode')
    async def qr_decode(request:Request):
        if request.headers.get('content-type','').split(';')[0] not in {'image/png','image/jpeg'}:
            raise HTTPException(415,'Send PNG/JPEG bytes, not multipart or remote URLs.')
        data=await request.body()
        from starlette.concurrency import run_in_threadpool
        try:
            text=await run_in_threadpool(decode_image,data)
        except ValueError as exc:
            raise HTTPException(422,str(exc)) from exc
        # Returned only to the submitting browser. Not logged, stored, or auto-checked.
        return {'text':text,'notice':'Decoded only, not verified. Inspect and approve before checking. The image was not saved.'}

    @app.post('/api/reports',status_code=201)
    def report(request:ReportRequest,authorization:str|None=Header(default=None)):
        if settings.demo:
            # Refused in the server, not hidden in the interface: a hosted demo must be
            # incapable of collecting real citizen evidence, which needs Gate C.
            raise HTTPException(403,'This is a public demonstration. Reports are not collected here, '
                                    'so nothing you write is stored. Use the official police reporting '
                                    'channel to file a real complaint.')
        result=scans.get(request.scan_id,bearer(authorization))
        # Citizens are anonymous, so consented reports land in the pilot organization's
        # intake queue. Routing to a chosen organization needs the partner agreements
        # in docs/BUILD_BACKLOG.md B06, not a field a caller can set.
        try: return store.report(result,request.model_dump(),DEFAULT_ORG_ID)
        except ValueError as exc: raise HTTPException(409,str(exc)) from exc

    @app.delete('/api/reports/{id_}',status_code=204)
    def delete_report(id_:str,authorization:str|None=Header(default=None)):
        if not store.delete(id_,bearer(authorization)):
            raise HTTPException(404,'Report not found or access denied.')
        return Response(status_code=204)

    @app.get('/api/scans/{id_}/export')
    def export(id_:str,authorization:str|None=Header(default=None)):
        result=public_result(scans.get(id_,bearer(authorization)))
        # Do not export tokens, correlation HMACs, unredacted messages or screenshots.
        evidence={'format':'trust-kh.review-summary.v1','generated_at':int(time.time()),
                  'assessment':result,'official_report_submitted':False,
                  'notice':'User-reviewed assessment summary; not certified forensic evidence. Preserve original evidence separately. This ZIP does not include original images or messages.'}
        raw=json.dumps(evidence,ensure_ascii=False,indent=2).encode()
        manifest=json.dumps({'summary.json':hashlib.sha256(raw).hexdigest(),
                             'note':'SHA-256 detects changes to this export; it does not prove a screenshot is authentic or establish chain of custody.'},indent=2).encode()
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('summary.json',raw)
            z.writestr('manifest.json',manifest)
            z.writestr('READ-ME.txt','This is not a police complaint. Review the contents, preserve originals separately, and use https://hotline.police.gov.kh/ to submit a complaint. Never share passwords or OTPs. No automatic submission or official integration has occurred.')
        return Response(buffer.getvalue(),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="trust-kh-review-summary.zip"'})

    @app.get('/api/analyst/reports')
    def report_list(authorization:str|None=Header(default=None)):
        principal=require(authorization,'reports.read')
        return {'reports':store.reports(principal.org_id),'organization':principal.org_id,
                'notice':'Reports belonging to your organization only. Accepted = reviewed for relevance, NOT a confirmed criminal allegation.'}

    @app.patch('/api/analyst/reports/{id_}')
    def review(id_:str,request:ReviewRequest,authorization:str|None=Header(default=None)):
        principal=require(authorization,'reports.review')
        # A report owned by another organization is reported as absent, not forbidden,
        # so the response cannot be used to probe for report identifiers.
        if not store.review(id_,request.status,request.reason,principal.org_id,principal):
            raise HTTPException(404,'Report not found.')
        return {'status':request.status,'reviewed_by':principal.email,
                'notice':'This does not add an indicator to a blocklist or change the risk engine.'}

    @app.get('/api/analyst/graph')
    def graph(authorization:str|None=Header(default=None)):
        principal=require(authorization,'graph.read')
        return store.graph(principal.org_id)

    @app.get('/api/analyst/audit')
    def audit(authorization:str|None=Header(default=None)):
        principal=require(authorization,'reports.read')
        return {'events':store.audit_trail(principal.org_id),
                'notice':'Audit history for your organization. Retained separately from report data.'}

    @app.get('/api/analyst/staff')
    def staff_list(authorization:str|None=Header(default=None)):
        principal=require(authorization,'staff.manage')
        return {'staff':directory.staff_list(principal.org_id),'organization':principal.org_id}

    @app.patch('/api/analyst/staff/{id_}')
    def staff_status(id_:str,request:StaffStatusRequest,authorization:str|None=Header(default=None)):
        principal=require(authorization,'staff.manage')
        if id_==principal.staff_id:
            raise HTTPException(409,'You cannot disable your own account.')
        if not directory.set_disabled(id_,principal.org_id,request.disabled,principal):
            raise HTTPException(404,'Staff account not found in your organization.')
        return {'staff_id':id_,'disabled':request.disabled}

    @app.get('/api/pulse')
    def pulse(authorization:str|None=Header(default=None)):
        principal=require(authorization,'pulse.read')
        return store.pulse(settings.minimum_cohort,principal.org_id)

    @app.get('/api/pulse/demo')
    def pulse_demo(authorization:str|None=Header(default=None)):
        principal=require(authorization,'pulse.read')
        return store.pulse(settings.minimum_cohort,principal.org_id,True)

    static=Path(__file__).parent/'static'
    app.mount('/',StaticFiles(directory=static,html=True),name='web')
    return app
