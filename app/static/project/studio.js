"use strict";
const names=["overview","architecture","experience","roadmap","pitch"];
function show(name){if(!names.includes(name))name="overview";document.querySelectorAll("[data-section]").forEach(el=>{el.hidden=el.dataset.section!==name;});document.querySelectorAll("[data-view]").forEach(el=>{const active=el.dataset.view===name;el.classList.toggle("active",active);el.setAttribute("aria-pressed",String(active));});}
document.querySelectorAll("[data-view]").forEach(el=>el.addEventListener("click",()=>{location.hash=el.dataset.view;show(el.dataset.view);}));
window.addEventListener("hashchange",()=>show(location.hash.slice(1)));show(location.hash.slice(1));
