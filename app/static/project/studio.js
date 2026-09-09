"use strict";
const names=["overview","architecture","experience","roadmap","pitch"];
function show(name){if(!names.includes(name))name="overview";document.querySelectorAll("[data-section]").forEach(el=>{el.hidden=el.dataset.section!==name;});document.querySelectorAll("[data-view]").forEach(el=>{const active=el.dataset.view===name;el.classList.toggle("active",active);el.setAttribute("aria-pressed",String(active));});}
document.querySelectorAll("[data-view]").forEach(el=>el.addEventListener("click",()=>{location.hash=el.dataset.view;show(el.dataset.view);}));
window.addEventListener("hashchange",()=>show(location.hash.slice(1)));show(location.hash.slice(1));
// Served two ways: by the application at /project/, and as static documentation on
// GitHub Pages where no application exists to link to.
const appLink=document.querySelector("[data-app-link]");
if(appLink&&!location.pathname.replace(/\/$/,"").endsWith("/project")){
 appLink.href="https://github.com/roosvelttetaing123-byte/Trust-KH";
 appLink.textContent="Source and setup on GitHub ↗";
}
