const assert=require('node:assert/strict');const path=require('node:path');
const c=require(path.join(process.env.COLLECTOR_ROOT||path.join(__dirname,'..'),'collection-core.js'));
const n=c.nodes[0],now=new Date(c.zoned('2026-10-12','08:10'));
const x=c.bundle({node:n,date:'2026-10-12',articles:[],sources:[],metrics:[{id:'ttf',name:'TTF',group:'energy',value:null,change_pct:3.2,baseline:20,verification_status:'MISSING'}],context:'',now});
assert.equal(x.metrics[0].change_pct,null,'Missing TTF must not retain its percent');assert.equal(x.metrics[0].baseline,null);
assert.ok(c.due(now,c.zoned('2026-10-12','07:30'),{}).some(e=>e.node.id==='N01'&&e.stage==='PREP'),'Resume must account for tasks missed over 15 minutes');
assert.equal(c.metricState({asset:'SP500',value:100,observed_at:'2026-10-09T20:00:00Z',period:'PROVIDER_QUOTE',verification_status:'UNVERIFIED'},now),'HISTORICAL_REFERENCE_NEEDS_SESSION_CHECK');
console.log('PASS regression: missing dependent values, recovery gap, session-aware reference labeling');
