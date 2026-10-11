'use strict';
(function(root){
const TZ='Europe/Bucharest';
const specs=[
['07:50','全天总备料','隔夜指数、能源、BET成分股公告与宏观日历',['international','energy','announcements','calendar']],
['08:00','上午开群资料','承接隔夜素材，补新公告与今日事件时间',['international','energy','announcements','calendar']],
['09:15','盘前观察资料','财报、评级、分红、资本事项、复权图表与流动性',['announcements','research','technical']],
['09:45','集合竞价资料','指示价格、昨收偏离、预期撮合量与委托不平衡',['auction']],
['10:00','开盘观察资料','实际开盘、首笔成交；10:05后补前5分钟数据',['opening']],
['11:30','午间研报资料','同口径同期成交、市场广度、观察池与上午问题',['intraday','context']],
['14:00','下午资讯资料','新增经济事实、公司事件、盘中变化与授权案例',['news','intraday','context']],
['16:00','国际联动资料','美股期货、US10Y基点、美元汇率、油气及BVB对照',['international','energy','intraday']],
['17:45','尾盘复盘资料','暂定尾盘快照、原始观察条件对照；最终公布后补采',['closing','context']],
['20:00','教授晚课资料','一三五技术，二四理念：最终资料、前课作业及白天问题',['lesson','context']],
['21:00','晚课互动资料','已采用课程、成员疑问、错误作业与相关证据',['context']],
['22:00','当日收束资料','全天有效对白、知识点、遗留问题与次日线索',['context','calendar']]
];
const requirements={
 international:['S&P500、Nasdaq、DAX、FTSE最近完整交易日收盘','标普/纳指期货、US10Y收益率与基点变化、DXY、USD/RON、EUR/RON（对应节点市场阶段）'],
 energy:['Brent与TTF：合约月份、价格、币种/单位、涨跌基准、观测时刻'],
 announcements:['当期BET成分股公告原文：隔夜财报、分红、增资、管理层、股东大会'],
 calendar:['INS/BNR/Eurostat/美国官方日历：事件、时区、公布时间、前值/预期来源/实际值'],
 research:['券商原始评级、报告日期、分红提案/批准/除权状态'],
 technical:['复权OHLC、均线/指标周期、关键位置依据、成交量同时间窗基准'],
 auction:['竞价指示价、昨收、预期撮合量、买卖不平衡/五档（有权限才使用）'],
 opening:['真实首笔时间/价格/数量、实际开盘价','开盘5分钟高低价与累计量、过去5个交易日同时段基准（数据形成后）'],
 intraday:['BET观测值、同范围成交额、上涨/下跌/平/停牌家数','观察股阶段高低价、累计量、最新价、时间戳与N03条件'],
 closing:['暂定/最终状态、官方收盘、尾盘成交占比及计算窗口','N03观察条件与结果，不倒改原预案'],
 news:['新增新闻全文/摘要、来源、发布/采集时间；原始政治描述保留作证据，前台只取经济事实'],
 lesson:['课纲及前课承接、技术/理念案例、相关财报/图表、计算口径及反例'],
 context:['用户提供的已采用对白、带消息引用的问题、作业、观察池或有授权案例（无聊天接口不自动获得）']
};
const minutes=t=>Number(t.slice(0,2))*60+Number(t.slice(3,5));
const hhmm=m=>`${String(Math.floor(m/60)).padStart(2,'0')}:${String(m%60).padStart(2,'0')}`;
const nodes=specs.map((s,i)=>({id:`N${String(i+1).padStart(2,'0')}`,legacyId:`w${s[0].replace(':','')}`,day:'weekday',pub:s[0],prep:hhmm(minutes(s[0])-15),title:s[1],focus:s[2],groups:s[3],mode:i>=9?'INTERNAL':'EXTERNAL',checks:s[3].flatMap(g=>requirements[g]),supplements:i===4?['10:05']:[]}));
function roParts(date=new Date()){
 const p=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:TZ,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(date).filter(x=>x.type!=='literal').map(x=>[x.type,x.value]));
 const day=new Date(`${p.year}-${p.month}-${p.day}T12:00:00Z`).getUTCDay();
 return {date:`${p.year}-${p.month}-${p.day}`,minute:minutes(`${p.hour}:${p.minute}`),day};
}
function zoned(date,time){let n=Date.parse(`${date}T${time}:00Z`);for(let i=0;i<3;i++){const p=roParts(new Date(n));n+=Date.parse(`${date}T${time}:00Z`)-Date.parse(`${p.date}T${hhmm(p.minute)}:00Z`)}return n;}
function malaysia(date,time){return new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Kuala_Lumpur',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date(zoned(date,time)));}
function due(now,previous,records){
 const p=roParts(now);if(p.day===0||p.day===6)return [];
 const start=previous==null?zoned(p.date,'00:00')-1:Math.max(previous,zoned(p.date,'00:00')-1);
 const events=[];
 for(const n of nodes)for(const [stage,time] of [['PREP',n.prep],...(n.mode==='EXTERNAL'?[['UPDATE',n.pub]]:[]),...n.supplements.map(t=>['SUPPLEMENT',t])]){
  const at=zoned(p.date,time),key=`${p.date}/${n.id}/${stage}/${time}`;
  const rec=records[key];
  if((at>start||rec?.status==='FAILED')&&at<=now.getTime()&&(!rec||rec.status==='FAILED')&&(!rec||!rec.retryAt||rec.retryAt<=now.getTime()))events.push({key,node:n,date:p.date,stage,scheduledAt:new Date(at).toISOString(),late:now.getTime()-at>60000});
 }
 return events;
}
function validateImport(data){
 if(!data||!Array.isArray(data.metrics))throw Error('必须包含metrics数组');
 if(data.metrics.length>500)throw Error('最多500项指标');
 const ids=new Set();
 for(const m of data.metrics){
  if(!m||typeof m.id!=='string'||!m.id||ids.has(m.id))throw Error('指标id必须非空且唯一');ids.add(m.id);
  if(typeof m.name!=='string'||!m.name||!Object.keys(requirements).includes(m.group))throw Error('指标名称或group无效');
  if(m.value!==null&&(typeof m.value!=='number'||!Number.isFinite(m.value)))throw Error('value必须为有限数值或null');
  if(m.value!==null&&(!m.unit||!Number.isFinite(Date.parse(m.observed_at))||!/^https:\/\//.test(m.source_url||'')))throw Error('有效数值必须带单位、时间与HTTPS来源');
  if(!['UNVERIFIED','USER_VERIFIED','HYPOTHESIS','MISSING'].includes(m.verification_status))throw Error('核验状态无效');
  if(m.verification_status==='USER_VERIFIED'&&(!m.verification_note||m.verification_note.length<8))throw Error('人工核验须有至少8字依据');
 }
 return data;
}
function metricState(m,now){if(m.value===null)return 'MISSING';if(m.verification_status==='HYPOTHESIS')return 'HYPOTHESIS';const age=now.getTime()-Date.parse(m.observed_at);if(age< -120000)return 'FUTURE_TIMESTAMP';if(m.period==='LAST_COMPLETED_SESSION')return 'HISTORICAL_SESSION';if(['SP500','NASDAQ','DAX','FTSE'].includes(m.asset)&&age>90*60000)return 'HISTORICAL_REFERENCE_NEEDS_SESSION_CHECK';return age>90*60000?'STALE':'AS_OF_TIMESTAMP';}
function bundle({node,date,articles,sources,metrics,context,collection,now=new Date()}){
 const at=now.toISOString(),boundary=zoned(date,node.prep),previous=nodes[nodes.indexOf(node)-1];
 const changeBoundary=previous?zoned(date,previous.pub):boundary-24*3600000;
 const news=articles.map(a=>({...a,nodeRelevance:'DIRECTOR_TO_SELECT',timeClass:!Number.isFinite(Date.parse(a.date))?'TIME_UNKNOWN':Date.parse(a.date)>now.getTime()?'FUTURE_TIMESTAMP':Date.parse(a.date)>=changeBoundary?'PUBLISHED_SINCE_PREVIOUS_NODE':'BACKGROUND',verification_status:a.verified?'USER_VERIFIED':'UNVERIFIED',political_context_flag:/guvern|politic|alegeri|parlament|ministru|partid|政府|选举|政治/i.test(`${a.title} ${a.description}`),heat_status:'HEURISTIC_NOT_VERIFIED_RANK'}));
 const relevant=metrics.filter(m=>node.groups.includes(m.group)).map(m=>({...m,...(m.value===null?{baseline:null,change_pct:null}:{}),data_state:metricState(m,now)}));
 return {schema_version:'4.0',story_date:date,timezone:TZ,node:{id:node.id,time:node.pub,collection_time:node.prep,malaysia_time:malaysia(date,node.pub),mode:node.mode},exported_at:at,collected_at:collection?.completedAt||at,collection_status:collection||null,source_status:sources,news_candidates:news,metrics:relevant,coverage:node.groups.map(group=>({group,requirements:requirements[group],status:relevant.some(m=>m.group===group&&m.value!==null)?'PARTIAL_REVIEW_REQUIRED':group==='context'&&context?'USER_CONTEXT_PROVIDED':'NOT_CONNECTED_OR_NOT_PROVIDED'})),user_context:context||'',editorial_instruction:'全面备料，普通资讯保留；导演选择内容和人物。不将采集成功或排序当事实核验。不推断机构身份、交易盈亏、政治动机。',missing_policy:'未接通或未提供的数据保持缺失；最终收盘与开盘5分钟数据须形成后补采；没有直接推送本会话的接口。'};
}
function text(b){return `【${b.node.id} ${b.node.time} 资讯资料包】\n故事日期：${b.story_date}；时区：${b.timezone}\n计划采集：${b.node.collection_time}；马来节点：${b.node.malaysia_time}\n实际采集完成：${b.collected_at||"尚未采集"}\n导出时间：${b.exported_at||b.collected_at}\n说明：这是待筛选资料，不是群聊对白。\n\n${JSON.stringify(b,null,2)}`;}
const api={nodes,requirements,minutes,roParts,zoned,malaysia,due,validateImport,bundle,text,metricState};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.BVB_COLLECTION=api;
})(typeof window==='undefined'?globalThis:window);
