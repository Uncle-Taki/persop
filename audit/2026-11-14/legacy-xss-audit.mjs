import { chromium } from '/tmp/perso-ui-audit/node_modules/playwright-core/index.mjs';
import fs from 'node:fs/promises';
const root='/home/mehdi/Project/leela/Perso';
const phase=process.argv[2]||'before';
const html=await fs.readFile(root+'/perso-mind/web/index.html','utf8');
const browser=await chromium.launch({executablePath:'/opt/google/chrome/chrome',headless:true,args:['--no-sandbox']});
try {
 const page=await browser.newPage();
 const attack='<img src="/missing-audit-image" onerror="window.__persoXSS=1">';
 await page.route('**/legacy-audit',r=>r.fulfill({contentType:'text/html',body:html}));
 await page.route('**/api/**',r=>r.fulfill({contentType:'application/json',body:JSON.stringify({success:true,data:r.request().url().endsWith('/sources')?[{id:'33333333-3333-3333-3333-333333333333',title:attack,source_type:'forum',capabilities:{},ingestion_status:'active'}]:[]})}));
 await page.goto('http://127.0.0.1:5317/legacy-audit',{waitUntil:'networkidle'});
 await page.evaluate(async()=>{window.__persoXSS=0;await loadWatchSources()});
 await page.waitForTimeout(300);
 const result=await page.evaluate(()=>({scriptExecuted:window.__persoXSS===1,titleText:document.getElementById('sources-table-body').textContent}));
 await fs.writeFile(root+`/audit/2026-11-14/evidence/legacy-xss-${phase}.json`,JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));
 if(phase==='after'&&result.scriptExecuted)process.exitCode=1;
} finally {await browser.close()}
