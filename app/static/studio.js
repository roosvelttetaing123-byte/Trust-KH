'use strict';
// Design-only fixture state. No network, storage, model or real-report side effects.
const $ = selector => document.querySelector(selector);
const samples = {
  warning: {text:'Pay a small fee to release your delivery. Send us your OTP to confirm. https://parcel-fee.test', title:'Strong warning signs', reason:'The fictional message requests that an OTP be sent to another person. The destination is a reserved demonstration domain, not a live threat finding.', action:'Do not share the OTP. Verify the request through an independently known official contact.', icon:'!', style:'caution'},
  unknown: {text:'https://unfamiliar-shop.example',title:'Unknown — not verified',reason:'An unfamiliar domain alone does not establish fraud or legitimacy. This preview has no live source that verifies the interaction.',action:'Pause and independently verify the seller and recipient. Do not treat missing evidence as approval to pay.',icon:'?',style:'unknown'},
  advice: {text:'Never share your OTP or password with another person.',title:'Unknown — not verified',reason:'This example advises against sharing a secret. Mentioning an OTP is not, by itself, a request to disclose one.',action:'Follow the advice, but do not infer the sender’s identity or the safety of a wider conversation.',icon:'?',style:'unknown'}
};
let sample='warning';
function resetResult(){ $('#sample-result').hidden=true; $('#sample-empty').hidden=false; }
function chooseSample(key){
  sample=key; $('#sample-text').value=samples[key].text;resetResult();
  document.querySelectorAll('[data-sample]').forEach(b=>{b.classList.toggle('active',b.dataset.sample===key);b.setAttribute('aria-pressed',String(b.dataset.sample===key));});
}
document.querySelectorAll('[data-sample]').forEach(b=>b.addEventListener('click',()=>chooseSample(b.dataset.sample)));
$('#explain-sample').addEventListener('click',()=>{
  const s=samples[sample];$('#sample-empty').hidden=true;$('#sample-result').hidden=false;
  $('#sample-verdict').className='verdict '+s.style;$('#verdict-title').textContent=s.title;$('#verdict-icon').textContent=s.icon;
  $('#sample-reason').textContent=s.reason;$('#sample-action').textContent=s.action;
});
$('#reset-sample').addEventListener('click',resetResult);
function selectView(name){
  if(!['check','desk','pulse'].includes(name))name='check';
  document.querySelectorAll('.view').forEach(v=>v.hidden=v.id!=='view-'+name);
  document.querySelectorAll('[data-view]').forEach(b=>{b.classList.toggle('selected',b.dataset.view===name);b.setAttribute('aria-pressed',String(b.dataset.view===name));});
}
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{selectView(b.dataset.view);history.replaceState(null,'','#'+b.dataset.view);}));
$('.wordmark').addEventListener('click',()=>selectView('check'));
const cases={delivery:['DEMO-001','Delivery fee message','A fictional message requests an OTP and a delivery fee. The customer selected only the relevant text and domain.','parcel-fee[.]test'],shopping:['DEMO-002','Unfamiliar seller link','A domain alone is insufficient. Request only relevant context through the authorized workflow; do not demand unrelated identification.','unfamiliar-shop[.]example'],advice:['DEMO-003','Security advice message','This message advises against disclosing an OTP. The reviewer should not treat the mention of a secret as a request for one.','No domain supplied']};
document.querySelectorAll('[data-case]').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('[data-case]').forEach(x=>x.classList.toggle('selected',x===b));
  const [id,title,copy,domain]=cases[b.dataset.case];$('#case-id').textContent=id+' / PRIVATE CASE VIEW';$('#case-title').textContent=title;$('#case-copy').textContent=copy;$('#case-domain').textContent=domain;$('#review-state').textContent='This button changes a sample state only. No case is saved.';
}));
$('#preview-review').addEventListener('click',()=>{$('#review-state').textContent='Sample decision: relevant for review. This is not a finding of fraud, a blocklist update, or a saved real report.';});
chooseSample('warning');selectView(location.hash.slice(1));
