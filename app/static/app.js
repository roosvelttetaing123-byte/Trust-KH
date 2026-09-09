import {km,resultCopy} from './i18n.js';
const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let lang='en';
try{lang=localStorage.getItem('trust-language')==='km'?'km':'en';}catch{}
let kind='message',last=null,receipt=null,imageLoaded=false,toastTimer;
const original=new Map($$('[data-i18n]').map(el=>[el,el.innerHTML]));
function translate(){
 document.documentElement.lang=lang;
 for(const [el,en]of original)el.innerHTML=lang==='km'?(km[el.dataset.i18n]||en):en; // Only trusted static dictionaries.
 $('#language').textContent=lang==='en'?'ខ្មែរ':'EN';
 $('#check-text').placeholder=lang==='km'?'បិទភ្ជាប់សារ ឬតំណ។ សូមលុប OTP លេខសម្ងាត់ និងព័ត៌មានផ្ទាល់ខ្លួនជាមុន។':'Paste a message or link here. Remove passwords, OTPs, account balances and personal details first.';
 if(last)renderResult();
}
$('#language').addEventListener('click',()=>{lang=lang==='en'?'km':'en';try{localStorage.setItem('trust-language',lang);}catch{}translate();});
function toast(message){$('#toast').textContent=message;$('#toast').classList.remove('hidden');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.add('hidden'),6500);}
async function api(path,{method='GET',body,token,headers={}}={}){
 const init={method,headers:{...headers},cache:'no-store'};
 if(token)init.headers.Authorization='Bearer '+token;
 if(body!==undefined){if(body instanceof Blob)init.body=body;else{init.headers['Content-Type']='application/json';init.body=JSON.stringify(body);}}
 let response;
 try{response=await fetch(path,init);}catch{throw Error('Connection unavailable. No assessment or report was completed.');}
 if(!response.ok){let message='Request failed.';try{message=(await response.json()).detail||message;}catch{}throw Error(message);}
 return response;
}
function saveBlob(blob,name){const link=document.createElement('a'),url=URL.createObjectURL(blob);link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),30000);}
function setKind(value){kind=value;$$('[data-kind]').forEach(b=>b.classList.toggle('active',b.dataset.kind===kind));}
$$('[data-kind]').forEach(b=>b.addEventListener('click',()=>setKind(b.dataset.kind)));
function navigate(page){if(!['check','analyst','pulse'].includes(page))page='check';$$('.page').forEach(p=>p.classList.toggle('hidden',p.id!=='page-'+page));$$('[data-page]').forEach(b=>b.classList.toggle('active',b.dataset.page===page));}
$$('[data-page]').forEach(b=>b.addEventListener('click',()=>{location.hash=b.dataset.page;}));
window.addEventListener('hashchange',()=>navigate(location.hash.slice(1)));
const examples={otp:{kind:'message',text:'You have won a reward. Send your OTP now. Claim at https://reward-check.test/claim and contact @helpdesk_demo. This is a synthetic demonstration.'},unknown:{kind:'url',text:'https://ordinary-shop.test/catalog'},advice:{kind:'message',text:'Never share your OTP with anyone. Contact your bank using a phone number you already know.'}};
$$('[data-example]').forEach(b=>b.addEventListener('click',()=>{const example=examples[b.dataset.example];setKind(example.kind);$('#check-text').value=example.text;$('#check-text').focus();}));
async function clearCheck(){
 const previous=last;last=null;receipt=null;$('#check-text').value='';$('#result-content').innerHTML='';$('#result-content').classList.add('hidden');$('#result-empty').classList.remove('hidden');
 $('#image-file').value='';$('#canvas-wrap').classList.add('hidden');imageLoaded=false;
 const canvas=$('#image-canvas');canvas.getContext('2d').clearRect(0,0,canvas.width,canvas.height);canvas.width=1;canvas.height=1;
 if(previous){try{await api('/api/scans/'+encodeURIComponent(previous.scan_id),{method:'DELETE',token:previous.access_token});}catch{toast('The local view was cleared. An unreachable server copy expires automatically after 15 minutes.');}}
}
$('#clear-check').addEventListener('click',clearCheck);
$('#run-check').addEventListener('click',async()=>{
 const text=$('#check-text').value.trim();if(!text){toast('Paste something to check first.');return;}
 const button=$('#run-check');button.disabled=true;
 try{const response=await api('/api/scans',{method:'POST',body:{kind,text}});last=await response.json();receipt=null;renderResult();if(window.innerWidth<651)$('#result-content').scrollIntoView({behavior:'smooth',block:'start'});}catch(error){toast(error.message);}finally{button.disabled=false;}
});
function renderResult(){
 const r=last,c=resultCopy[lang];$('#result-empty').classList.add('hidden');const el=$('#result-content');el.classList.remove('hidden');
 el.innerHTML=`<div class="verdict-box ${esc(r.verdict)}">${r.is_demo?`<span class="synthetic">${esc(c.demo)}</span>`:''}<div class="verdict-label">${esc(c[r.verdict])}</div><p>${esc(c.notice)}</p></div>
 <div class="result-section-title">${esc(c.reasons)}</div>${r.signals.length?r.signals.map(s=>`<div class="signal"><p>${esc(s[lang]||s.en)}</p><small>${esc(s.rule_id)} · ${esc(s.source)}</small></div>`).join(''):`<p class="field-note">${esc(c.noSignals)}</p>`}
 ${r.indicators.length?`<div class="result-section-title">${esc(c.indicators)}</div><div class="chip-row">${r.indicators.map(i=>`<span class="chip">${esc(i.kind)} · ${esc(i.display)}</span>`).join('')}</div>`:''}
 ${r.payment?`<div class="result-section-title">${esc(c.payment)}</div><p class="field-note">${esc(c.unsupported)} ${esc(c.qrNotice)}</p><div class="chip-row">${Object.entries(r.payment.fields||{}).map(([k,v])=>`<span class="chip">${esc(k)}: ${esc(v)}</span>`).join('')}<span class="chip">CRC: ${r.payment.crc_valid?'pass':'not confirmed'}</span></div>`:''}
 <div class="result-section-title">${esc(c.coverage)}</div><div class="coverage"><span class="yes">${esc(c.rules)}</span><span>${esc(c.feeds)}</span><span>${esc(c.bank)}</span><span>${esc(c.visit)}</span></div>
 <div class="result-section-title">${esc(c.next)}</div><ol class="steps">${c.steps.map(s=>`<li>${esc(s)}</li>`).join('')}</ol>
 <div class="result-actions"><button class="button secondary" id="export-summary">${esc(c.export)}</button><button class="button quiet" id="forget-result">${esc(c.forgot)}</button></div>
 <a class="field-note" href="https://hotline.police.gov.kh/" target="_blank" rel="noopener noreferrer">${esc(c.official)}</a>
 <p class="field-note">${esc(c.checked)} ${esc(r.rule_version)}</p>
 <details class="report-form"><summary>${esc(c.report)}</summary><div class="report-fields"><select id="report-category" aria-label="Scam category">${['impersonation','investment','shopping','job','other'].map((v,i)=>`<option value="${v}">${esc(c.categories[i])}</option>`).join('')}</select><select id="report-channel" aria-label="Message channel">${['telegram','facebook','messenger','sms','web','other'].map((v,i)=>`<option value="${v}">${esc(c.channels[i])}</option>`).join('')}</select></div><label class="checkbox"><input type="checkbox" id="report-consent"><span>${esc(c.consent)}</span></label><button class="button primary" id="submit-report">${esc(c.submit)}</button><div id="report-receipt"></div></details>`;
 $('#forget-result').addEventListener('click',clearCheck);
 $('#export-summary').addEventListener('click',async()=>{try{const response=await api('/api/scans/'+encodeURIComponent(r.scan_id)+'/export',{token:r.access_token});saveBlob(await response.blob(),'trust-kh-review-summary.zip');}catch(error){toast(error.message);}});
 $('#submit-report').addEventListener('click',async()=>{
  if(!$('#report-consent').checked){toast('Please review and explicitly agree to the report consent.');return;}
  const button=$('#submit-report');button.disabled=true;
  try{const response=await api('/api/reports',{method:'POST',token:r.access_token,body:{scan_id:r.scan_id,consent:true,consent_version:'2026-09-09.v1',category:$('#report-category').value,channel:$('#report-channel').value}});receipt=await response.json();showReceipt();}catch(error){toast(error.message);button.disabled=false;}
 });
 if(receipt)showReceipt();
}
function showReceipt(){const c=resultCopy[lang];$('#submit-report').disabled=true;$('#report-receipt').innerHTML=`<div class="success">${esc(c.success)}<div class="button-row"><button class="button secondary" id="save-receipt">${esc(c.receipt)}</button></div><p class="field-note">${esc(c.receiptHint)}</p></div>`;$('#save-receipt').addEventListener('click',()=>saveBlob(new Blob([JSON.stringify(receipt,null,2)],{type:'application/json'}),'trust-kh-private-receipt.json'));}
$('#withdraw-report').addEventListener('click',async()=>{const file=$('#receipt-file').files[0];if(!file||file.size>10000){toast('Choose a valid small receipt JSON file.');return;}try{const r=JSON.parse(await file.text());if(!/^[a-f0-9]{32}$/.test(r.report_id)||typeof r.deletion_token!=='string'||r.deletion_token.length>128)throw Error('Invalid receipt.');await api('/api/reports/'+r.report_id,{method:'DELETE',token:r.deletion_token});toast('Report and related observations were deleted.');$('#receipt-file').value='';}catch(error){toast(error.message);}});
const canvas=$('#image-canvas'),ctx=canvas.getContext('2d');let start=null;
$('#image-file').addEventListener('change',async()=>{const file=$('#image-file').files[0];if(!file)return;if(!['image/png','image/jpeg'].includes(file.type)||file.size>2*1024*1024){toast('Use PNG/JPEG up to 2 MiB.');return;}try{const bitmap=await createImageBitmap(file);if(bitmap.width*bitmap.height>6000000){bitmap.close();throw Error('Resize the image to at most 6 megapixels.');}const scale=Math.min(1,1200/Math.max(bitmap.width,bitmap.height));canvas.width=Math.round(bitmap.width*scale);canvas.height=Math.round(bitmap.height*scale);ctx.drawImage(bitmap,0,0,canvas.width,canvas.height);bitmap.close();imageLoaded=true;$('#canvas-wrap').classList.remove('hidden');}catch(error){toast(error.message);}});
function point(event){const rect=canvas.getBoundingClientRect();return{x:(event.clientX-rect.left)*canvas.width/rect.width,y:(event.clientY-rect.top)*canvas.height/rect.height};}
canvas.addEventListener('pointerdown',event=>{if(imageLoaded){start=point(event);canvas.setPointerCapture(event.pointerId);}});
canvas.addEventListener('pointerup',event=>{if(!start)return;const end=point(event);ctx.fillStyle='#000';ctx.fillRect(Math.min(start.x,end.x),Math.min(start.y,end.y),Math.abs(end.x-start.x),Math.abs(end.y-start.y));start=null;});
canvas.addEventListener('pointercancel',()=>{start=null;});
const canvasBlob=()=>new Promise((resolve,reject)=>canvas.toBlob(blob=>blob?resolve(blob):reject(Error('Could not encode image.')),'image/png'));
$('#save-image').addEventListener('click',async()=>{try{saveBlob(await canvasBlob(),'trust-kh-redacted-copy.png');}catch(error){toast(error.message);}});
$('#decode-qr').addEventListener('click',async()=>{const button=$('#decode-qr');button.disabled=true;try{const blob=await canvasBlob();if(blob.size>2*1024*1024)throw Error('Redacted image exceeds 2 MiB. Resize or crop it first.');const response=await api('/api/qr/decode',{method:'POST',body:blob,headers:{'Content-Type':'image/png'}});const result=await response.json();setKind('qr');$('#check-text').value=result.text;toast('QR decoded, not verified. Inspect the text, then choose Check.');}catch(error){toast(error.message);}finally{button.disabled=false;}});
async function loadAnalyst(){
 const token=$('#analyst-key').value.trim();
 try{const [a,b]=await Promise.all([api('/api/analyst/reports',{token}),api('/api/analyst/graph',{token})]);const {reports}=await a.json(),graph=await b.json();$('#analyst-content').classList.remove('hidden');
  $('#report-list').innerHTML=reports.length?reports.map(r=>`<div class="report-item"><h3>${esc(r.category)} <span class="status">${esc(r.status)}</span></h3><p>${r.is_demo?'SYNTHETIC DEMO · ':''}${esc(r.channel)} · ${esc(r.id.slice(0,8))}</p><div class="chip-row">${r.indicators.map(i=>`<span class="chip">${esc(i.display)}</span>`).join('')}</div><p>Rule findings: ${esc(r.signal_codes.join(', ')||'none')}. No original message retained.</p><div class="button-row"><button class="button secondary" data-review="accepted" data-id="${esc(r.id)}">Accept relevance</button><button class="button quiet" data-review="rejected" data-id="${esc(r.id)}">Reject / insufficient</button></div></div>`).join(''):'<p class="field-note">No reports yet. Submit a separate opt-in report from a check, or run scripts/seed_demo.py for labelled synthetic data.</p>';
  $$('[data-review]').forEach(button=>button.addEventListener('click',async()=>{try{await api('/api/analyst/reports/'+encodeURIComponent(button.dataset.id),{method:'PATCH',token,body:{status:button.dataset.review,reason:button.dataset.review==='accepted'?'relevant_evidence':'insufficient_evidence'}});await loadAnalyst();}catch(error){toast(error.message);}}));
  const nodeMap=Object.fromEntries(graph.nodes.map(n=>[n.id,n]));
  $('#graph').innerHTML=graph.nodes.length?`<div class="graph-nodes">${graph.nodes.map(n=>`<div class="graph-node"><strong>${esc(n.label)}</strong><small>${esc(n.kind)} · ${n.reports} reviewed report(s) ${n.is_demo?'· DEMO':''}</small></div>`).join('')}</div>${graph.edges.map(e=>`<div class="edge">${esc(nodeMap[e.source].label)} ↔ ${esc(nodeMap[e.target].label)}<br>${e.reports} co-occurrence(s), not attribution</div>`).join('')}`:'<p class="field-note">No reviewed associations. Approve relevant reports before a connection can appear.</p>';
 }catch(error){toast(error.message);}
}
$('#load-analyst').addEventListener('click',loadAnalyst);
$('#lock-analyst').addEventListener('click',()=>{$('#analyst-key').value='';$('#analyst-content').classList.add('hidden');$('#report-list').innerHTML='';$('#graph').innerHTML='';});
$('#load-pulse').addEventListener('click',async()=>{try{const response=await api($('#pulse-demo').checked?'/api/pulse/demo':'/api/pulse',{token:$('#pulse-key').value.trim()});const data=await response.json();$('#pulse-content').innerHTML=`<article class="panel pulse-card"><div class="eyebrow">${data.dataset==='synthetic_demo'?'SYNTHETIC DEMONSTRATION DATA':'CONSENTED, REVIEWED REPORTS ONLY'}</div><h2>Signals, with boundaries.</h2><div class="metric">${data.reviewed_reports===null?'Suppressed':esc(data.reviewed_reports)}</div><p class="field-note">Reviewed submitted reports — not unique victims or verified incidents.</p>${data.categories.map(c=>`<div class="bar-row"><span>${esc(c.category)}</span><strong>${esc(c.reports)} reports</strong></div>`).join('')||'<p class="field-note">No category meets the minimum publication threshold.</p>'}<p class="field-note">Minimum cell size: ${data.minimum_cell_size}. ${data.small_cells_suppressed?'Small cells and the total were withheld to avoid subtraction disclosure.':''}</p><p class="field-note">${esc(data.notice)}</p></article>`;}catch(error){toast(error.message);}});
$('#lock-pulse').addEventListener('click',()=>{$('#pulse-key').value='';$('#pulse-content').innerHTML='';});
function online(){ $('#offline').classList.toggle('hidden',navigator.onLine);$('#run-check').disabled=!navigator.onLine; }
window.addEventListener('online',online);window.addEventListener('offline',online);
if('serviceWorker'in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{});
translate();navigate(location.hash.slice(1));online();
