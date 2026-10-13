/* Browser acceptance for the 65-person trading PR.
 * Runs only against an ephemeral loopback server with isolated fictional data.
 */
const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');

const PORT = 18765;
const BASE = 'http://127.0.0.1:' + PORT;
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'trading-65-browser-'));
const artifacts = path.resolve('build/trading-browser-qa');
fs.mkdirSync(artifacts, {recursive:true});
const server = spawn('python', ['-u', 'tools/finance_skill_api.py', '--host','127.0.0.1',
  '--port',String(PORT),'--data-dir',dir], {stdio:['ignore','pipe','pipe']});
server.stdout.on('data', c=>process.stdout.write(c));
server.stderr.on('data', c=>process.stderr.write(c));
const pause = ms=>new Promise(r=>setTimeout(r,ms));
async function waitServer(){
 for(let i=0;i<70;i++){
  if(server.exitCode!==null) throw Error('Python service exited with '+server.exitCode);
  try{const r=await fetch(BASE+'/healthz');if(r.ok)return;}
  catch{}
  await pause(400);
 }
 throw Error('Local Python server failed to start');
}
async function state(page){const r=await page.request.get(BASE+'/api/trading/sim/state');assert.equal(r.status(),200);return r.json();}
async function waitStored(page, revision){
 await page.waitForFunction(revision=>document.querySelector('#sim-message')?.textContent?.includes('账本版本 '+revision),revision,{timeout:12000});
}
async function actClick(page, selector, oldRevision){
 await page.locator(selector).click();
 await waitStored(page,oldRevision+1);
}
async function setField(page, id, value){await page.locator('#'+id).fill(String(value));}
async function acceptDialogs(page){page.on('dialog',d=>d.accept());}
async function main(){
 await waitServer();
 const browser=await chromium.launch({channel:'chrome',headless:true,args:['--no-sandbox']});
 const errors=[];
 const page=await browser.newPage({viewport:{width:1440,height:810},deviceScaleFactor:1});
 page.on('pageerror', e=>errors.push(String(e)));
 page.on('console', m=>{if(m.type()==='error')errors.push('console: '+m.text());});
 await acceptDialogs(page);
 try{
  await page.goto(BASE+'/trading',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>document.querySelector('#sim-message')?.textContent?.includes('读取成功'),null,{timeout:15000});
  assert.match(await page.title(),/交易中心/);
  assert.equal(await page.locator('#sim-people-table tbody tr').count(),65);
  let s=await state(page);
  assert.equal(s.people.length,65);assert.equal(s.transactions.length,0);assert.equal(s.holdings.length,0);
  assert.equal(fs.existsSync(path.join(dir,'trading-65.json')),false,'Reads must not fabricate transactions');
  // A viewport-size screenshot is readable; never shrink a 3000+ pixel page into one preview.
  await page.screenshot({path:path.join(artifacts,'01-desktop-overview-1440x810.png'),fullPage:false});
  await page.locator('#sim-people-table').screenshot({path:path.join(artifacts,'02-desktop-members-readable.png')});
  for(const pid of ['01','02']){
   await page.locator('#sim-member').selectOption(pid);
   await page.locator('#sim-opened').selectOption('1');
   await page.locator('#sim-currency').selectOption('RON');
   await setField(page,'sim-funds',1000);
   await page.locator('#sim-frequency').selectOption('HIGH');
   await actClick(page,'#sim-save-member',s.revision);
   s=await state(page);
   assert.equal(s.people.find(p=>p.id===pid).opened,true);
  }
  await setField(page,'sim-symbol','QATEST');
  await setField(page,'sim-stock-name','浏览器验收模拟股票');
  await setField(page,'sim-market','BVB');
  await page.locator('#sim-offer-currency').selectOption('RON');
  await setField(page,'sim-price',10);
  await setField(page,'sim-min-shares',5);
  await setField(page,'sim-hold-days',0);
  await setField(page,'sim-participants',2);
  await actClick(page,'#sim-create-offer',s.revision);
  s=await state(page);
  assert.equal(s.offers.length,1);
  const offerId=s.offers[0].id;
  await page.locator('#sim-load-offer').click();
  assert.equal(await page.locator('#sim-price').inputValue(),'10');
  await setField(page,'sim-price',11);
  await actClick(page,'#sim-edit-offer',s.revision);
  s=await state(page);
  assert.equal(s.offers[0].unit_price,11);
  await actClick(page,'#sim-recommend',s.revision);
  s=await state(page);
  assert.equal(s.recommendations.length,1);
  assert.equal(s.recommendations[0].candidates.length,2);
  for(const pid of ['01','02']){
   await actClick(page,'[data-person-card="'+pid+'"] [data-sim-action="invite"]',s.revision);
   s=await state(page);
   await actClick(page,'[data-person-card="'+pid+'"] [data-sim-action="buy"]',s.revision);
   s=await state(page);
  }
  assert.equal(s.holdings.length,2);
  assert.equal(s.transactions.length,2);
  assert.equal(s.stock_groups.length,1);
  assert.equal(s.stock_groups[0].holding_members,2);
  assert.equal(await page.locator('#sim-stock-chart .sim-stock-bar').count(),1);
  await page.locator('#sim-holdings').screenshot({path:path.join(artifacts,'03-desktop-holdings-readable.png')});
  await page.locator('#sim-stock-chart').screenshot({path:path.join(artifacts,'04-desktop-stocks-readable.png')});
  await page.screenshot({path:path.join(artifacts,'05-desktop-workspace-1440x810.png'),fullPage:false});
  const selected=page.locator('#sim-holdings [data-batch-holding]');
  assert.equal(await selected.count(),2);
  await selected.nth(0).check();await selected.nth(1).check();
  await setField(page,'sim-batch-price',12);
  await actClick(page,'#sim-batch-sell',s.revision);
  s=await state(page);
  assert.equal(s.holdings.filter(x=>x.status==='sold').length,2);
  assert.equal(s.transactions.length,4);
  assert.equal(s.stock_groups.length,0);
  assert.equal(new Set(s.transactions.filter(t=>t.type==='sell').map(t=>t.batch_id)).size,1);
  assert.ok(fs.existsSync(path.join(dir,'trading-65.json')),'Saved ledger should persist');
  await page.reload();
  await page.waitForFunction(()=>document.querySelector('#sim-message')?.textContent?.includes('读取成功'),null,{timeout:15000});
  const persisted=await state(page);
  assert.equal(persisted.transactions.length,4);
  assert.equal(await page.locator('#sim-transactions tbody tr').count(),4);
  const invalid=await page.request.post(BASE+'/api/trading/sim/action',{
   data:{action:'eligibility',person_id:'70',opened:true,currency:'RON',funds:100}
  });
  assert.equal(invalid.status(),400,'Old 70-person identity must be rejected');
  const afterInvalid=await state(page);
  assert.equal(afterInvalid.revision,s.revision);
  await page.setViewportSize({width:390,height:844});
  await page.reload();
  await page.waitForFunction(()=>document.querySelector('#sim-message')?.textContent?.includes('读取成功'),null,{timeout:15000});
  await page.locator('#sim-people-search').fill('01');
  assert.equal(await page.locator('#sim-people-table tbody tr').count(),1);
  const measure=await page.evaluate(()=>({
   viewport:innerWidth,documentWidth:document.documentElement.scrollWidth,
   bodyWidth:document.body.scrollWidth
  }));
  assert.ok(measure.documentWidth<=measure.viewport+4,
    'Mobile horizontal overflow: '+JSON.stringify(measure));
  await page.evaluate(()=>{window.scrollTo(0,0);document.documentElement.scrollTop=0;document.body.scrollTop=0;});
  await pause(250);
  await page.screenshot({path:path.join(artifacts,'06-mobile-overview-390x844.png'),fullPage:false});
  await page.locator('#sim-holdings').screenshot({path:path.join(artifacts,'07-mobile-holdings-readable.png')});
  assert.deepEqual(errors,[],'No browser JavaScript errors');
  console.log('BROWSER_QA_PASS',{
   member_count:s.people.length,offers:s.offers.length,
   persisted_transactions:persisted.transactions.length,
   sold_holdings:afterInvalid.metrics.sold_records,
   mobile_width:measure.documentWidth, screenshots:artifacts
  });
 } finally{await browser.close();}
}
main().catch(e=>{console.error('BROWSER_QA_FAIL',e.stack||String(e));process.exitCode=1;})
 .finally(()=>{server.kill('SIGTERM');});
