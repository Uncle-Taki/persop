import { chromium } from '/tmp/perso-ui-audit/node_modules/playwright-core/index.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';

const root=path.dirname(new URL(import.meta.url).pathname);
const browser=await chromium.launch({executablePath:'/opt/google/chrome/chrome',headless:true,args:['--no-sandbox']});
const results=[];
try {
 for (const [width,height] of [[360,800],[390,844],[430,932],[1440,900]]) {
  const context=await browser.newContext({viewport:{width,height},locale:'fa-IR'});
  const page=await context.newPage();const errors=[],apiRequests=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.url().includes('/api/'))apiRequests.push(r.url())});
  await page.goto('http://127.0.0.1:5317/',{waitUntil:'networkidle'});
  await page.screenshot({path:path.join(root,'screenshots',`best-offers-${width}x${height}.png`),fullPage:false});
  const metrics=await page.evaluate(()=>{
   const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom,right:r.right}};
   const nav=document.querySelector('nav[aria-label]'),navR=nav.getBoundingClientRect();
   const cards=[...document.querySelectorAll('article')].map((e,i)=>({index:i,text:e.innerText.slice(0,120),...rect(e)}));
   const controls=[...document.querySelectorAll('button,input,select,textarea')];
   return {title:document.title,lang:document.documentElement.lang,dir:document.documentElement.dir,viewport:{width:innerWidth,height:innerHeight},documentWidth:document.documentElement.scrollWidth,nav:rect(nav),tabs:[...nav.querySelectorAll('button')].map(e=>({text:e.innerText,...rect(e)})),cards,fullyVisibleCards:cards.filter(r=>r.y>=0&&r.bottom<=navR.y).length,smallTargets:controls.filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&(r.width<44||r.height<44)}).map(e=>({tag:e.tagName,name:e.getAttribute('aria-label')||e.getAttribute('title')||e.innerText,...rect(e)})),images:document.images.length,headings:[...document.querySelectorAll('h1,h2,h3')].map(e=>({tag:e.tagName,text:e.innerText})),tokens:Object.fromEntries(['primary','primary-hover','accent','soft-mint','bg','surface','text-primary','text-secondary','border'].map(k=>[k,getComputedStyle(document.documentElement).getPropertyValue('--color-'+k).trim()])),inputs:controls.filter(e=>['INPUT','SELECT','TEXTAREA'].includes(e.tagName)).map(e=>({tag:e.tagName,type:e.type,placeholder:e.getAttribute('placeholder'),labels:e.labels?.length,ariaLabel:e.getAttribute('aria-label')}))};
  });
  await page.evaluate(()=>window.scrollTo(0,document.documentElement.scrollHeight));
  await page.waitForTimeout(200);
  metrics.lastCardAfterScroll=await page.locator('article').last().boundingBox();
  metrics.apiRequests=apiRequests;metrics.pageErrors=errors;
  if(width===390){
   await page.locator('nav[aria-label] button').nth(2).click();
   await page.screenshot({path:path.join(root,'screenshots','telegram-sources-390x844.png')});
   await fs.writeFile(path.join(root,'evidence','sources-screen.txt'),await page.locator('body').innerText());
   await page.locator('nav[aria-label] button').nth(4).click();
   await page.screenshot({path:path.join(root,'screenshots','settings-390x844.png')});
   await page.locator('nav[aria-label] button').nth(3).click();
   await page.screenshot({path:path.join(root,'screenshots','conversations-390x844.png')});
  }
  results.push(metrics);await context.close();
 }
 await fs.writeFile(path.join(root,'evidence','browser-baseline.json'),JSON.stringify(results,null,2));
 console.log(JSON.stringify(results.map(r=>({viewport:r.viewport,fullyVisibleCards:r.fullyVisibleCards,overflow:r.documentWidth>r.viewport.width,smallTargets:r.smallTargets.length,images:r.images,tabs:r.tabs.map(t=>t.text),pageErrors:r.pageErrors,apiRequests:r.apiRequests})),null,2));
} finally {await browser.close()}
