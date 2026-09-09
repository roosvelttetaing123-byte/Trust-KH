import {LANGS, dict, resultCopy, messages} from './i18n.js';
import {citizenCopy, resultOverrides} from './citizen-i18n.js';
const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let lang='km';
try{const saved=localStorage.getItem('trust-language');if(LANGS.includes(saved))lang=saved;}catch{}
let kind='message',last=null,receipt=null,imageLoaded=false,toastTimer,demoMode=false;
let scanSequence=0,activeScan=null,pdfController=null,pdfBusy=false,checkFailed=false;
let imageSequence=0,decodeController=null,decoding=false,openingImage=false;
const original=new Map($$('[data-i18n]').map(el=>[el,el.innerHTML]));
const originalLabels=new Map($$('[data-i18n-label]').map(el=>[el,el.getAttribute('aria-label')]));
const u=()=>citizenCopy[lang];
const t=key=>u()[key]??(lang==='km'?null:dict[lang]?.[key])??null;
const msg=()=>messages[lang];
const field=()=>$('#check-'+({message:'text',url:'url',phone:'phone',qr:'qr'}[kind]));
let checkStatusKey='',qrStatusKey='',checkErrorKey='',qrErrorKey='';
function status(which,key){
 if(which==='check')checkStatusKey=key;else qrStatusKey=key;
 $('#'+which+'-status').textContent=key?u()[key]:'';
}
function showError(which,key){
 if(which==='check')checkErrorKey=key;else qrErrorKey=key;
 const el=$('#'+which+'-error');el.textContent=key?u()[key]:'';el.classList.toggle('hidden',!key);
}
function failure(error,fallback='unavailable'){
 if(error.name==='AbortError')return 'timeout';
 if(error.status===404)return 'expired';
 if(error.status===429)return 'rateLimited';
 if(error.status===422)return 'invalid';
 if(error.status===503)return 'unavailable';
 if(error.network)return 'connection';
 return fallback;
}
function syncWork(){
 $('#run-check').disabled=!!activeScan||!navigator.onLine;
 $('#run-check').setAttribute('aria-busy',String(!!activeScan));
 $('#run-check .working-mark').classList.toggle('hidden',!activeScan);
 $('#check-button-label').textContent=activeScan?u().checking:(checkFailed?u().retry:u().runCheck);
 $('#decode-qr').disabled=decoding||openingImage||!imageLoaded||!navigator.onLine;
 $('#decode-qr').setAttribute('aria-busy',String(decoding));
 $('#decode-qr').textContent=decoding?u().decoding:u().decodeQr;
 const pdf=$('#export-summary');if(pdf){pdf.disabled=pdfBusy;pdf.setAttribute('aria-busy',String(pdfBusy));pdf.textContent=pdfBusy?u().preparingPdf:u().export;}
}
function translate(){
 document.documentElement.lang=lang;
 for(const [el,base] of original)el.innerHTML=t(el.dataset.i18n)??base;
 for(const [el,base] of originalLabels)el.setAttribute('aria-label',t(el.dataset.i18nLabel)??base);
 $('#check-text').placeholder=u().checkPlaceholder;
 $('#image-canvas').setAttribute('aria-label',u().uploadTitle);
 $('#language').value=lang;
 if(demoMode){
  $('[data-i18n="prototype"]').textContent=msg().demoBadge;
  $('[data-i18n="prototypeNote"]').textContent=u().demoNotice;
  $('.withdraw').classList.add('hidden');
 }
 renderAuth();if(last)renderResult();
 status('check',checkStatusKey);status('qr',qrStatusKey);
 showError('check',checkErrorKey);showError('qr',qrErrorKey);syncWork();
}
$('#language').addEventListener('change',event=>{
 if(!LANGS.includes(event.target.value))return;
 lang=event.target.value;
 try{localStorage.setItem('trust-language',lang);}catch{}
 translate();
});
function toast(message){$('#toast').textContent=message;$('#toast').classList.remove('hidden');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.add('hidden'),6500);}
async function api(path,{method='GET',body,token,headers={},signal}={}){
 const init={method,headers:{...headers},cache:'no-store',signal};
 if(token)init.headers.Authorization='Bearer '+token;
 if(body!==undefined){if(body instanceof Blob)init.body=body;else{init.headers['Content-Type']='application/json';init.body=JSON.stringify(body);}}
 let response;
 try{response=await fetch(path,init);}catch(error){if(error.name==='AbortError')throw error;throw Object.assign(Error(msg().connection),{network:true});}
 if(!response.ok){let message=msg().requestFailed;try{message=(await response.json()).detail||message;}catch{}throw Object.assign(Error(message),{status:response.status});}
 return response;
}
function saveBlob(blob,name){const link=document.createElement('a'),url=URL.createObjectURL(blob);link.href=url;link.download=name;document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);}
function cancelCheck(){
 scanSequence++;activeScan?.abort();activeScan=null;
 pdfController?.abort();pdfController=null;pdfBusy=false;
 checkFailed=false;status('check','');showError('check','');syncWork();
}
function hideResult(){last=null;receipt=null;$('#result-content').replaceChildren();$('#result-content').classList.add('hidden');$('#result-panel').classList.add('hidden');}
function invalidate(){cancelCheck();hideResult();}
function cancelDecode(){imageSequence++;decodeController?.abort();decodeController=null;decoding=false;openingImage=false;status('qr','');showError('qr','');syncWork();}
function setKind(value){
 if(!['message','url','phone','qr'].includes(value))return;
 if(kind!==value){invalidate();cancelDecode();}
 kind=value;
 $$('[data-kind]').forEach(b=>{b.classList.toggle('active',b.dataset.kind===kind);b.setAttribute('aria-pressed',String(b.dataset.kind===kind));});
 $$('[data-input]').forEach(el=>el.classList.toggle('hidden',el.dataset.input!==kind));
}
$$('[data-kind]').forEach(b=>b.addEventListener('click',()=>setKind(b.dataset.kind)));
function navigate(page){
 if(!['check','analyst','pulse'].includes(page))page='check';
 if(page!=='check'){cancelCheck();cancelDecode();}
 $$('.page').forEach(p=>p.classList.toggle('hidden',p.id!=='page-'+page));
 $$('[data-page]').forEach(b=>{b.classList.toggle('active',b.dataset.page===page);if(b.dataset.page===page)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
}
$$('[data-page]').forEach(b=>b.addEventListener('click',()=>{location.hash=b.dataset.page;}));
window.addEventListener('hashchange',()=>navigate(location.hash.slice(1)));
const examples={otp:{kind:'message',text:'You have won a reward. Send your OTP now. Claim at https://reward-check.test/claim and contact @helpdesk_demo. This is a synthetic demonstration.'},unknown:{kind:'url',text:'https://ordinary-shop.test/catalog'},advice:{kind:'message',text:'Never share your OTP with anyone. Contact your bank using a phone number you already know.'}};
$$('[data-example]').forEach(b=>b.addEventListener('click',()=>{const example=examples[b.dataset.example];invalidate();setKind(example.kind);field().value=example.text;field().focus();}));
$$('[data-input] textarea,[data-input] input:not([type=file]):not([type=checkbox])').forEach(input=>input.addEventListener('input',()=>{
 invalidate();if(input.id==='check-qr'){$('#qr-confirm').checked=false;cancelDecode();}
}));
$('#qr-confirm').addEventListener('change',invalidate);
async function clearCheck(){
 const previous=last;invalidate();removeImage();
 for(const id of ['check-text','check-url','check-phone','check-qr'])$('#'+id).value='';
 status('check','cleared');
 if(previous){try{await api('/api/scans/'+encodeURIComponent(previous.scan_id),{method:'DELETE',token:previous.access_token});}catch{toast(msg().clearedLocal);}}
}
$('#clear-check').addEventListener('click',clearCheck);
async function runCheck(){
 if(activeScan||!navigator.onLine)return;
 const text=field().value.trim();
 if(!text){showError('check','pasteFirst');(kind==='qr'?$('#image-file'):field()).focus();return;}
 if(kind==='qr'&&!$('#qr-confirm').checked){showError('check','confirmFirst');$('#qr-manual').open=true;$('#qr-confirm').focus();return;}
 invalidate();const sequence=scanSequence,controller=new AbortController();activeScan=controller;
 const deadline=setTimeout(()=>controller.abort(),25000);
 status('check','checking');syncWork();
 try{
  const response=await api('/api/scans',{method:'POST',body:{kind,text},signal:controller.signal});
  const result=await response.json();if(sequence!==scanSequence)return;
  last=result;receipt=null;renderResult();status('check','complete');
  $('#result-panel').focus({preventScroll:true});
  $('#result-panel').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});
 }catch(error){if(sequence===scanSequence){checkFailed=true;status('check','');showError('check',failure(error));}}
 finally{clearTimeout(deadline);if(sequence===scanSequence){activeScan=null;syncWork();}}
}
$('#run-check').addEventListener('click',runCheck);
for(const id of ['check-url','check-phone'])$('#'+id).addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();runCheck();}});
function renderResult(){
 const r=last,c={...resultCopy[lang],...resultOverrides[lang]};$('#result-empty').classList.add('hidden');$('#result-panel').classList.remove('hidden');
 const el=$('#result-content');el.classList.remove('hidden');
 el.innerHTML=`<div class="verdict-box ${esc(r.verdict)}">${r.is_demo?`<span class="synthetic">${esc(c.demo)}</span>`:''}<div class="verdict-label">${esc(c[r.verdict])}</div><p>${esc(c.notice)}</p></div>
 <h3 class="result-section-title">${esc(c.reasons)}</h3>${r.signals.length?r.signals.map(s=>`<div class="signal"><p>${esc(s[lang]||s.en)}</p></div>`).join(''):`<p class="field-note">${esc(c.noSignals)}</p>`}
 <h3 class="result-section-title">${esc(c.next)}</h3><ol class="steps">${c.steps.map(s=>`<li>${esc(s)}</li>`).join('')}</ol>
 <div class="result-actions"><button class="button secondary" id="export-summary">${esc(u().export)}</button><button class="button quiet" id="forget-result">${esc(c.forgot)}</button></div>
 <p id="pdf-status" role="status" aria-live="polite" class="work-status"></p><div id="pdf-error" role="alert" class="inline-error hidden"></div>
 <details class="result-details"><summary>${esc(u().details)}</summary>
 ${r.indicators.length?`<h3 class="result-section-title">${esc(c.indicators)}</h3><div class="chip-row">${r.indicators.map(i=>`<span class="chip">${esc(i.display)}</span>`).join('')}</div>`:''}
 ${r.payment?`<h3 class="result-section-title">${esc(c.payment)}</h3><p class="field-note">${esc(c.unsupported)} ${esc(c.qrNotice)}</p>`:''}
 <h3 class="result-section-title">${esc(c.coverage)}</h3><div class="coverage"><span class="yes">${esc(c.rules)}</span><span>${esc(c.feeds)}</span><span>${esc(c.bank)}</span><span>${esc(c.visit)}</span></div>
 ${r.signals.map(s=>`<p class="field-note">${esc(s.rule_id)} · ${esc(s.source)}</p>`).join('')}
 <p class="field-note">${esc(c.checked)} ${esc(r.rule_version)}</p></details>
 <p><a class="field-note" href="https://hotline.police.gov.kh/" target="_blank" rel="noopener noreferrer">${esc(c.official)}</a></p>
 ${demoMode?`<p class="field-note demo-note">${esc(u().demoNotice)}</p>`:`<details class="report-form"><summary>${esc(c.report)}</summary><div class="report-fields"><select id="report-category" aria-label="${esc(c.categoryLabel)}">${['impersonation','investment','shopping','job','other'].map((v,i)=>`<option value="${v}">${esc(c.categories[i])}</option>`).join('')}</select><select id="report-channel" aria-label="${esc(c.channelLabel)}">${['telegram','facebook','messenger','sms','web','other'].map((v,i)=>`<option value="${v}">${esc(c.channels[i])}</option>`).join('')}</select></div><label class="checkbox"><input type="checkbox" id="report-consent"><span>${esc(c.consent)}</span></label><button class="button primary" id="submit-report">${esc(c.submit)}</button><div id="report-receipt"></div></details>`}`;
 $('#forget-result').addEventListener('click',clearCheck);
 $('#export-summary').addEventListener('click',()=>downloadPdf(r));
 $('#submit-report')?.addEventListener('click',async()=>{
  if(!$('#report-consent').checked){toast(msg().consentFirst);return;}
  const button=$('#submit-report');button.disabled=true;
  try{const response=await api('/api/reports',{method:'POST',token:r.access_token,body:{scan_id:r.scan_id,consent:true,consent_version:'2026-09-09.v1',category:$('#report-category').value,channel:$('#report-channel').value}});const saved=await response.json();if(last!==r)return;receipt=saved;showReceipt();}catch(error){toast(error.message);button.disabled=false;}
 });
 if(receipt)showReceipt();syncWork();
}
async function downloadPdf(result){
 if(pdfBusy||last!==result)return;
 const controller=new AbortController();pdfController=controller;pdfBusy=true;
 const language=lang,deadline=setTimeout(()=>controller.abort(),45000);
 $('#pdf-error').classList.add('hidden');$('#pdf-status').textContent=u().preparingPdf;syncWork();
 try{
  const response=await api('/api/scans/'+encodeURIComponent(result.scan_id)+'/export?lang='+encodeURIComponent(language),{token:result.access_token,signal:controller.signal});
  if(!(response.headers.get('content-type')||'').startsWith('application/pdf'))throw Error('PDF expected');
  const blob=await response.blob();if(last!==result||controller.signal.aborted)return;
  saveBlob(blob,'trust-kh-check-summary-'+language+'.pdf');$('#pdf-status').textContent=u().pdfReady;
 }catch(error){if(last===result&&pdfController===controller){$('#pdf-status').textContent='';$('#pdf-error').textContent=u()[failure(error,'pdfFailed')];$('#pdf-error').classList.remove('hidden');}}
 finally{clearTimeout(deadline);if(pdfController===controller){pdfController=null;pdfBusy=false;syncWork();}}
}
function showReceipt(){const c=resultCopy[lang];$('#submit-report').disabled=true;$('#report-receipt').innerHTML=`<div class="success">${esc(c.success)}<div class="button-row"><button class="button secondary" id="save-receipt">${esc(c.receipt)}</button></div><p class="field-note">${esc(c.receiptHint)}</p></div>`;$('#save-receipt').addEventListener('click',()=>saveBlob(new Blob([JSON.stringify(receipt,null,2)],{type:'application/json'}),'trust-kh-private-receipt.json'));}
$('#withdraw-report').addEventListener('click',async()=>{const file=$('#receipt-file').files[0];if(!file||file.size>10000){toast(msg().receiptInvalid);return;}try{const r=JSON.parse(await file.text());if(!/^[a-f0-9]{32}$/.test(r.report_id)||typeof r.deletion_token!=='string'||r.deletion_token.length>128)throw Error(msg().receiptInvalid);await api('/api/reports/'+r.report_id,{method:'DELETE',token:r.deletion_token});toast(msg().withdrawn);$('#receipt-file').value='';}catch(error){toast(error.message);}});
const canvas=$('#image-canvas'),ctx=canvas.getContext('2d');let start=null;
function removeImage(resetSelection=true){
 cancelDecode();imageLoaded=false;start=null;if(resetSelection)$('#image-file').value='';$('#canvas-wrap').classList.add('hidden');
 ctx.clearRect(0,0,canvas.width,canvas.height);canvas.width=1;canvas.height=1;
 $('#check-qr').value='';$('#qr-confirm').checked=false;$('#qr-manual').open=false;
 if(kind==='qr')invalidate();syncWork();
}
$('#remove-image').addEventListener('click',removeImage);
async function loadImage(file){
 removeImage(false);if(!file)return;
 if(!['image/png','image/jpeg'].includes(file.type)||file.size>2*1024*1024){showError('qr','imageInvalid');return;}
 const sequence=imageSequence;openingImage=true;status('qr','loadingImage');syncWork();
 try{
  const bitmap=await createImageBitmap(file);
  if(sequence!==imageSequence){bitmap.close();return;}
  if(bitmap.width*bitmap.height>6000000){bitmap.close();throw Error('size');}
  const scale=Math.min(1,1200/Math.max(bitmap.width,bitmap.height));canvas.width=Math.round(bitmap.width*scale);canvas.height=Math.round(bitmap.height*scale);
  ctx.drawImage(bitmap,0,0,canvas.width,canvas.height);bitmap.close();imageLoaded=true;$('#canvas-wrap').classList.remove('hidden');status('qr','imageReady');
 }catch(error){if(sequence===imageSequence){status('qr','');showError('qr',error.message==='size'?'imageInvalid':'imageFailed');}}
 finally{if(sequence===imageSequence){openingImage=false;syncWork();}}
}
$('#image-file').addEventListener('change',event=>loadImage(event.target.files[0]));
const dropzone=$('#qr-dropzone');
for(const event of ['dragenter','dragover'])dropzone.addEventListener(event,e=>{e.preventDefault();dropzone.classList.add('dragging');});
for(const event of ['dragleave','drop'])dropzone.addEventListener(event,e=>{e.preventDefault();dropzone.classList.remove('dragging');});
dropzone.addEventListener('drop',e=>{if(e.dataTransfer.files.length===1)loadImage(e.dataTransfer.files[0]);else showError('qr','imageInvalid');});
function point(event){const rect=canvas.getBoundingClientRect();return{x:(event.clientX-rect.left)*canvas.width/rect.width,y:(event.clientY-rect.top)*canvas.height/rect.height};}
canvas.addEventListener('pointerdown',event=>{if(imageLoaded){start=point(event);canvas.setPointerCapture(event.pointerId);}});
canvas.addEventListener('pointerup',event=>{if(!start)return;const end=point(event);ctx.fillStyle='#000';ctx.fillRect(Math.min(start.x,end.x),Math.min(start.y,end.y),Math.abs(end.x-start.x),Math.abs(end.y-start.y));start=null;cancelDecode();$('#check-qr').value='';$('#qr-confirm').checked=false;invalidate();});
canvas.addEventListener('pointercancel',()=>{start=null;});
const canvasBlob=()=>new Promise((resolve,reject)=>canvas.toBlob(blob=>blob?resolve(blob):reject(Error('image')),'image/png'));
$('#save-image').addEventListener('click',async()=>{if(!imageLoaded)return;try{saveBlob(await canvasBlob(),'trust-kh-redacted-copy.png');}catch{showError('qr','imageFailed');}});
$('#decode-qr').addEventListener('click',async()=>{
 if(decoding||!imageLoaded)return;
 invalidate();cancelDecode();const sequence=imageSequence,controller=new AbortController();decodeController=controller;decoding=true;
 $('#qr-confirm').checked=false;$('#check-qr').value='';status('qr','decoding');syncWork();
 const deadline=setTimeout(()=>controller.abort(),25000);
 try{
  const blob=await canvasBlob();if(sequence!==imageSequence)return;
  if(blob.size>2*1024*1024)throw Error('size');
  const response=await api('/api/qr/decode',{method:'POST',body:blob,headers:{'Content-Type':'image/png'},signal:controller.signal});
  const result=await response.json();if(sequence!==imageSequence)return;
  $('#check-qr').value=result.text;$('#qr-manual').open=true;status('qr','qrDecoded');$('#check-qr').focus();
 }catch(error){if(sequence===imageSequence){status('qr','');showError('qr',error.message==='size'?'imageInvalid':error.status===422?'qrFailed':failure(error,'qrFailed'));}}
 finally{clearTimeout(deadline);if(sequence===imageSequence){decodeController=null;decoding=false;syncWork();}}
});
// The session token is deliberately kept in memory only: a reload signs the analyst
// out rather than leaving evidence access recoverable from browser storage.
let session=null,me=null;
function renderAuth(){
 const m=msg();
 for(const panel of $$('[data-auth-panel]')){
  const view=panel.dataset.authPanel;
  if(!session){
   panel.innerHTML=`<h2>${esc(m.signInTitle)}</h2><p class="field-note">${esc(m.signInNote)}</p>
   <div class="report-fields"><div class="auth-field"><label class="field-label" for="email-${view}">${esc(m.emailLabel)}</label><input id="email-${view}" type="email" autocomplete="username"></div>
   <div class="auth-field"><label class="field-label" for="password-${view}">${esc(m.passwordLabel)}</label><input id="password-${view}" type="password" autocomplete="current-password"></div></div>
   <div class="button-row"><button class="button primary" data-signin="${view}">${esc(m.signIn)}</button></div>`;
  }else if(!me?.mfa_satisfied){
   panel.innerHTML=`<h2>${esc(m.mfaTitle)}</h2><p class="field-note">${esc(m.mfaNote)}</p>
   <div class="access-row"><input id="mfa-${view}" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="6" aria-label="${esc(m.mfaLabel)}">
   <button class="button primary" data-mfa="${view}">${esc(m.verify)}</button>
   <button class="button quiet" data-signout="1">${esc(m.signOut)}</button></div>`;
  }else{
   panel.innerHTML=`<div class="access-row signed-in">
   <div><strong>${esc(m.signedInAs)} ${esc(me.display_name)}</strong>
   <p class="field-note">${esc(m.organizationLabel)}: ${esc(me.organization)} · ${esc(m.roleLabel)}: ${esc(me.role)} · ${esc(me.email)}</p></div>
   <button class="button quiet" data-signout="1">${esc(m.signOut)}</button></div>`;
  }
 }
 const analystOk=me?.mfa_satisfied&&(me.role==='analyst'||me.role==='admin');
 const pulseOk=me?.mfa_satisfied&&(me.role==='pulse'||me.role==='admin');
 $('#analyst-content').classList.toggle('hidden',!analystOk);
 $('#pulse-controls').classList.toggle('hidden',!pulseOk);
 if(!analystOk){$('#report-list').innerHTML='';$('#graph').innerHTML='';$('#audit-log').innerHTML='';}
 if(!pulseOk)$('#pulse-content').innerHTML='';
}
document.addEventListener('click',async event=>{
 const signin=event.target.closest('[data-signin]'),mfa=event.target.closest('[data-mfa]'),out=event.target.closest('[data-signout]');
 if(signin){
  const view=signin.dataset.signin,button=signin;button.disabled=true;
  try{
   const response=await api('/api/auth/login',{method:'POST',body:{email:$(`#email-${view}`).value.trim(),password:$(`#password-${view}`).value}});
   session=(await response.json()).session;me={mfa_satisfied:false};renderAuth();
   $(`#mfa-${view}`)?.focus();
  }catch(error){toast(error.message);button.disabled=false;}
 }else if(mfa){
  const view=mfa.dataset.mfa;mfa.disabled=true;
  try{
   await api('/api/auth/mfa',{method:'POST',token:session,body:{code:$(`#mfa-${view}`).value.trim()}});
   me=await (await api('/api/auth/me',{token:session})).json();renderAuth();
   if(me.role==='analyst'||me.role==='admin')await loadAnalyst();
  }catch(error){toast(error.message);mfa.disabled=false;}
 }else if(out){
  try{await api('/api/auth/logout',{method:'POST',token:session});}catch{}
  session=null;me=null;renderAuth();toast(msg().signedOut);
 }
});
async function loadAnalyst(){
 const token=session,m=msg();
 try{const [a,b,c]=await Promise.all([api('/api/analyst/reports',{token}),api('/api/analyst/graph',{token}),api('/api/analyst/audit',{token})]);const {reports}=await a.json(),graph=await b.json(),{events}=await c.json();
  $('#audit-log').innerHTML=events.length?events.map(e=>`<div class="edge"><strong>${esc(e.event)}</strong>${e.actor_email?' · '+esc(e.actor_email):''}<br>${esc(new Date(e.timestamp*1000).toLocaleString())}${e.reason?' · '+esc(e.reason):''}</div>`).join(''):`<p class="field-note">${esc(m.auditEmpty)}</p>`;
  $('#report-list').innerHTML=reports.length?reports.map(r=>`<div class="report-item"><h3>${esc(r.category)} <span class="status">${esc(r.status)}</span></h3><p>${r.is_demo?esc(m.syntheticData)+' · ':''}${esc(r.channel)} · ${esc(r.id.slice(0,8))}</p><div class="chip-row">${r.indicators.map(i=>`<span class="chip">${esc(i.display)}</span>`).join('')}</div><p>${esc(m.ruleFindings)}: ${esc(r.signal_codes.join(', ')||m.none)}. ${esc(m.noOriginal)}</p><div class="button-row"><button class="button secondary" data-review="accepted" data-id="${esc(r.id)}">${esc(m.accept)}</button><button class="button quiet" data-review="rejected" data-id="${esc(r.id)}">${esc(m.reject)}</button></div></div>`).join(''):`<p class="field-note">${esc(m.noReports)}</p>`;
  $$('[data-review]').forEach(button=>button.addEventListener('click',async()=>{try{await api('/api/analyst/reports/'+encodeURIComponent(button.dataset.id),{method:'PATCH',token:session,body:{status:button.dataset.review,reason:button.dataset.review==='accepted'?'relevant_evidence':'insufficient_evidence'}});await loadAnalyst();}catch(error){toast(error.message);}}));
  const nodeMap=Object.fromEntries(graph.nodes.map(n=>[n.id,n]));
  $('#graph').innerHTML=graph.nodes.length?`<div class="graph-nodes">${graph.nodes.map(n=>`<div class="graph-node"><strong>${esc(n.label)}</strong><small>${esc(n.kind)} · ${esc(n.reports)} ${esc(m.reviewedReports)} ${n.is_demo?'· DEMO':''}</small></div>`).join('')}</div>${graph.edges.map(e=>`<div class="edge">${esc(nodeMap[e.source].label)} ↔ ${esc(nodeMap[e.target].label)}<br>${esc(e.reports)} ${esc(m.coOccurrence)}</div>`).join('')}`:`<p class="field-note">${esc(m.noAssoc)}</p>`;
 }catch(error){toast(error.message);}
}
$('#load-pulse').addEventListener('click',async()=>{const m=msg();try{const response=await api($('#pulse-demo').checked?'/api/pulse/demo':'/api/pulse',{token:session});const data=await response.json();$('#pulse-content').innerHTML=`<article class="panel pulse-card"><div class="eyebrow">${esc(data.dataset==='synthetic_demo'?m.syntheticData:m.consentedData)}</div><h2>${esc(m.pulseTitle)}</h2><div class="metric">${data.reviewed_reports===null?esc(m.suppressed):esc(data.reviewed_reports)}</div><p class="field-note">${esc(m.pulseMetricNote)}</p>${data.categories.map(c=>`<div class="bar-row"><span>${esc(c.category)}</span><strong>${esc(c.reports)} ${esc(m.reports)}</strong></div>`).join('')||`<p class="field-note">${esc(m.noThreshold)}</p>`}<p class="field-note">${esc(m.minCell)}: ${esc(data.minimum_cell_size)}. ${data.small_cells_suppressed?esc(m.smallCells):''}</p><p class="field-note">${esc(data.notice)}</p></article>`;}catch(error){toast(error.message);}});
function online(){ $('#offline').classList.toggle('hidden',navigator.onLine);syncWork(); }
window.addEventListener('online',online);window.addEventListener('offline',online);
if('serviceWorker'in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{});
translate();setKind(kind);navigate(location.hash.slice(1));online();
// The server is the authority on whether report intake is enabled; the interface
// only reflects it.
fetch('/api/capabilities',{cache:'no-store'}).then(r=>r.json()).then(caps=>{
 if(caps.report_intake===false){demoMode=true;translate();}
}).catch(()=>{});
