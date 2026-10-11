// Trusted Playwright smoke check. Requires a real approved preview host and test credentials.
import { chromium } from 'playwright';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';

const specPath = process.env.GATE_BROWSER_SPEC;
const username = process.env.GATE_TEST_USERNAME;
const password = process.env.GATE_TEST_PASSWORD;
const approvedBase = process.env.GATE_APPROVED_BASE_URL;
const approvedHost = process.env.GATE_ALLOWED_HOST;
if (!specPath || !username || !password || !approvedBase || !approvedHost) {
  console.error('BLOCK: browser spec, approved host and test-login credentials are required');
  process.exit(2);
}
let spec;
try { spec = JSON.parse(await readFile(specPath, 'utf8')); }
catch { console.error('BLOCK: invalid browser spec'); process.exit(2); }
if (!Array.isArray(spec.routes) || !spec.routes.length ||
    !spec.login?.username_selector || !spec.login?.password_selector || !spec.login?.submit_selector || !spec.login?.success_selector) {
  console.error('BLOCK: missing routes or login steps'); process.exit(2);
}
let approvedUrl;
try {
  approvedUrl = new URL(approvedBase);
  if (approvedUrl.hostname !== approvedHost || approvedUrl.protocol !== 'https:' || approvedUrl.username || approvedUrl.password) throw Error();
} catch { console.error('BLOCK: non-approved preview host'); process.exit(2); }
function inside(path) {
  const url = new URL(path, approvedUrl);
  if (url.origin !== approvedUrl.origin) throw new Error('off-origin route rejected');
  return url;
}
const sizes = [{name:'desktop',width:1920,height:1080}, {name:'laptop',width:1366,height:768}, {name:'mobile',width:390,height:844}];
const errors=[];
await mkdir('browser-evidence', {recursive:true});
const browser = await chromium.launch({headless:true});
try {
  for (const size of sizes) {
    const page = await browser.newPage({viewport: {width:size.width,height:size.height}});
    page.on('pageerror', e => errors.push(`${size.name}: Javascript error ${e.name}`));
    try {
      await page.goto(inside(spec.login.path ?? '/login'), {waitUntil:'domcontentloaded',timeout:20000});
      if (new URL(page.url()).origin !== approvedUrl.origin) throw new Error('login redirected outside approved host');
      await page.locator(spec.login.username_selector).fill(username);
      await page.locator(spec.login.password_selector).fill(password);
      const submit = page.locator(spec.login.submit_selector);
      await submit.evaluate(button => {
        const form = button.closest('form') ||
          (button.getAttribute('form') ? document.getElementById(button.getAttribute('form')) : null);
        if (form && form.action && new URL(form.action, window.location.href).origin !== window.location.origin) {
          throw new Error('form action targets another origin');
        }
      });
      await submit.click();
      if (spec.login.otp_selector) {
        if (!process.env.GATE_TEST_OTP) throw new Error('OTP required; no test OTP supplied');
        await page.locator(spec.login.otp_selector).fill(process.env.GATE_TEST_OTP);
        if (spec.login.otp_submit_selector) await page.locator(spec.login.otp_submit_selector).click();
      }
      await page.locator(spec.login.success_selector).waitFor({state:'visible',timeout:15000});
      for (const entry of spec.routes) {
        if (!entry.path || !entry.ready_selector) throw new Error('incomplete required route config');
        await page.goto(inside(entry.path), {waitUntil:'domcontentloaded',timeout:20000});
        if (new URL(page.url()).origin !== approvedUrl.origin) throw new Error('route redirected outside approved host');
        const target = page.locator(entry.ready_selector);
        await target.waitFor({state:'visible',timeout:15000});
        if (entry.expected_text) {
          const visible = await target.innerText();
          if (!visible.includes(entry.expected_text)) throw new Error(`missing required text at ${entry.path}`);
        }
        const metrics = await page.evaluate(() => ({scroll:document.documentElement.scrollWidth,
          viewport:document.documentElement.clientWidth,bodyLength:document.body.innerText.trim().length}));
        if (metrics.scroll > metrics.viewport + 2) throw new Error(`horizontal overflow at ${entry.path}`);
        if (metrics.bodyLength < 20) throw new Error(`blank page at ${entry.path}`);
        const short = entry.path.replaceAll(/[^a-zA-Z0-9]/g,'_').slice(0,60) || 'root';
        await page.screenshot({path:resolve('browser-evidence', `${size.name}-${short}.png`),fullPage:true});
      }
    } catch(e) {
      errors.push(`${size.name}: ${e.message.replaceAll(username,'[redacted]').replaceAll(password,'[redacted]')}`);
    } finally { await page.close(); }
  }
} finally { await browser.close(); }
await writeFile('browser-evidence/browser-result.json', JSON.stringify({status:errors.length?'BLOCK':'PASS',
  tested_viewports:sizes,route_count:spec.routes.length,issues:errors},null,2));
if(errors.length){console.error(`BLOCK: ${errors.join('; ')}`);process.exit(1)}
console.log('Browser login, route visibility and viewport smoke passed');
