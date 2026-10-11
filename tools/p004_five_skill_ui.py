"""Embedded P004 five-Skill operator panel for the existing /skill route."""
PANEL = r"""
<section id="p004-five-skills" class="p004-root" aria-label="P004五个独立Skill">
  <style>
  .p004-root{margin:4px 0 24px;background:linear-gradient(125deg,#fff,#f8fafc);border:1px solid #dae2ea;border-radius:17px;padding:20px;box-shadow:0 9px 28px #26394d0c;color:#243242}
  .p004-root *{box-sizing:border-box}.p004-root h2{font-size:19px;margin:0}.p004-root p{font-size:12px;color:#526379;line-height:1.65}
  .p004-title{display:flex;align-items:center;gap:12px;flex-wrap:wrap;justify-content:space-between}.p004-status{font-size:12px;color:#7e6139;background:#f5efe3;padding:5px 9px;border-radius:7px}
  .p004-roles{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;margin:15px 0}
  .p004-role{background:#f4f6f8;border:1px solid #e0e6ec;border-radius:10px;padding:9px;font-size:12px;color:#334557;font-weight:700;text-align:center}
  .p004-role small{display:block;font-size:10px;color:#768391;font-weight:500}
  .p004-form{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
  .p004-form label{font-size:12px;font-weight:700;display:block}
  .p004-form input,.p004-form select,.p004-root textarea{width:100%;background:white;border:1px solid #ccd6e0;border-radius:8px;margin-top:6px;padding:9px;font:inherit;color:#213447}
  .p004-root textarea{min-height:95px;font-size:12px;line-height:1.55;resize:vertical}
  #p004-json{min-height:130px;font-family:Consolas,monospace;font-size:12px}
  #p004-prompt{min-height:105px;font-size:11px}
  .p004-line{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
  .p004-root button{cursor:pointer;border:1px solid #becbd8;border-radius:8px;background:#f5f7fa;color:#25384c;padding:9px 13px;min-height:38px;font:inherit;font-weight:750}
  .p004-root button.p004-primary{background:#224759;border-color:#224759;color:white}
  .p004-root button:disabled{opacity:.45;cursor:not-allowed}
  #p004-feedback{white-space:pre-wrap;overflow-wrap:anywhere;min-height:38px;padding:10px;background:#f0f3f7;border:1px solid #e0e6ec;border-radius:9px;font-size:12px}
  #p004-preview{max-height:190px;overflow:auto}.p004-speech{border-top:1px solid #e1e5e9;padding:7px 0;white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}
  .p004-speech strong{font-size:11px;color:#26546e}
  .p004-confirm{display:flex;align-items:center;gap:7px;font-size:12px;margin:6px 0}.p004-confirm input{width:auto}
  .p004-root hr{border:0;border-top:1px solid #e3e7ed;margin:15px 0}
  @media(max-width:820px){.p004-roles{grid-template-columns:repeat(2,minmax(0,1fr))}.p004-form{grid-template-columns:1fr 1fr}}
  @media(max-width:480px){.p004-form{grid-template-columns:1fr}.p004-root{padding:14px}}
  </style>
  <div class="p004-title"><h2>总导演 × 编剧 × 教授 × 助理 × 65人成员</h2><span class="p004-status" id="p004-stage">检查中</span></div>
  <p>五个独立 Skill 在四合一模块三协作。全新65人候选与旧版人物历史隔离；正式采用前保留人工确认。不能把虚构群聊当成真人股票群发言。</p>
  <div class="p004-roles">
    <div class="p004-role">01 总导演<small>话题／选角／节奏</small></div>
    <div class="p004-role">02 编剧<small>自然对白／连续剧情</small></div>
    <div class="p004-role">03 教授<small>晚间课程／口吻</small></div>
    <div class="p004-role">04 助理<small>白天主持／问答</small></div>
    <div class="p004-role">05 成员<small>65人独立人格</small></div>
  </div>
  <p id="p004-actual-state">正在读取服务器真实角色名单。</p>
  <div class="p004-form">
    <label>场次编号<input id="p004-scene" value="scene-20261014-a" maxlength="80"></label>
    <label>故事日期<input id="p004-date" type="date" value="2026-10-14"></label>
    <label>时段<select id="p004-daypart"><option value="morning">上午</option><option value="afternoon">下午</option><option value="evening">晚间</option></select></label>
    <label>候选成员数<select id="p004-max"><option>4</option><option selected>8</option><option>12</option><option>15</option></select></label>
    <label style="grid-column:span 2">虚构题材关键词（逗号分隔）<input id="p004-topic" value="能源,交通" maxlength="300"></label>
  </div>
  <label style="font-size:12px;font-weight:700;display:block;margin-top:10px">导演临时插播指令
    <textarea id="p004-override" maxlength="1000" placeholder="例如：这次先让质疑者提问，助理回应，其他成员可以沉默。"></textarea>
  </label>
  <div class="p004-line"><button type="button" class="p004-primary" id="p004-plan">导演真实选角 → 编剧任务</button><button type="button" id="p004-copy" disabled>复制完整编剧任务</button></div>
  <p id="p004-cast">本场尚未选择人物。</p>
  <textarea id="p004-prompt" readonly placeholder="完成选角后，这里会有可复制给现有ChatGPT的完整人物口吻和背景任务。"></textarea>
  <hr>
  <div class="p004-title"><h2>剧情审稿与人物记忆</h2><small style="color:#65788a">不要求本机安装模型／不产生伪AI结果</small></div>
  <p>把现有 ChatGPT 实际生成的罗马尼亚语对白 JSON 粘贴到这里；点击校验会真正检查身份、时间、历史引用和风险内容。</p>
  <textarea id="p004-json" spellcheck="false" placeholder="粘贴AI生成的完整剧本 JSON"></textarea>
  <div class="p004-line"><button type="button" class="p004-primary" id="p004-review" disabled>实际审核剧本</button><button type="button" id="p004-copy-json">复制当前剧本</button></div>
  <div id="p004-feedback" role="status" aria-live="polite">未生成剧本，也未通过审稿。</div>
  <div id="p004-preview"></div>
  <hr>
  <p><b>正式采用</b>：只有正式批准65名新人物、完成文学与事实审读，并双重确认后才能写入独立 SQLite 记忆。当前不会自动发 WhatsApp。</p>
  <label class="p004-confirm"><input id="p004-editor" type="checkbox">编辑已经人工审阅罗马尼亚语口吻、事实与剧情</label>
  <label class="p004-confirm"><input id="p004-operator" type="checkbox">操作者确认将这一场纳入小说正式历史</label>
  <div class="p004-line"><button type="button" id="p004-adopt" disabled>确认采用并写入独立记忆</button></div>
  <hr>
  <div class="p004-title"><h2>新65人人设逐人审核</h2><span class="p004-status" id="p004-approved-count">0 / 65 正式批准</span></div>
  <p>独立新角色与旧版本无关。选定人物后查看职业、地区、性格及罗马尼亚语样句，确认后才纳入正式名册；不提供一键假批准。</p>
  <label style="font-size:12px;font-weight:700;display:block">选择待审核人物
    <select id="p004-person-select"><option value="">读取服务器真实候选…</option></select>
  </label>
  <pre id="p004-profile" style="max-height:210px;overflow:auto;white-space:pre-wrap;word-break:break-word;background:#f6f8fa;padding:12px;border-radius:9px;font:12px/1.65 'Microsoft YaHei',monospace"></pre>
  <label class="p004-confirm"><input id="p004-person-reviewed" type="checkbox">我已核对该人物的人设、地区及罗马尼亚语表达</label>
  <label class="p004-confirm"><input id="p004-person-confirmed" type="checkbox">我确认采用当前显示的这一个人物为新故事正式角色</label>
  <div class="p004-line"><button type="button" id="p004-approve-person" disabled>批准所选人物（仅这1人）</button></div>

</section>
"""
SCRIPT = r"""
<script>
(function(){
"use strict";
const $=id=>document.getElementById(id);
const root=$("p004-five-skills");if(!root)return;
let token=null, approved=0, valid=false;
const stage=v=>$("p004-stage").textContent=v;
const feedback=v=>$("p004-feedback").textContent=v;
async function getStatus(){
 const r=await fetch("/api/p004/status",{credentials:"same-origin"});const data=await r.json();
 if(!r.ok)throw Error(data.error||"状态读取失败");
 approved=data.approved_count;
 $("p004-actual-state").textContent="新人物候选："+data.candidate_count+"人；正式批准："+approved+"人；自动AI编剧："+(data.autonomous_writer_connected?"已接通":"未接通（复用现有ChatGPT手动交接）")+"；模拟交易联动："+(data.module_two_transaction_linked?"已接通":"未接通");
 $("p004-adopt").disabled=!valid||approved!==65;
 stage(approved===65?"角色已批准":"人物待批准");
}
async function call(action,payload){
 const response=await fetch("/api/p004/"+action,{credentials:"same-origin",method:"POST",
 headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
 let data=await response.json();if(!response.ok)throw Error(data.error||"请求未成功");
 return data;
}
$("p004-plan").onclick=async()=>{
 try{
  const request={
   scene_id:$("p004-scene").value.trim(),
   story_date:$("p004-date").value,
   daypart:$("p004-daypart").value,
   topic_keywords:$("p004-topic").value.split(/[,，、]/).map(x=>x.trim()).filter(Boolean),
   max_members:Number($("p004-max").value),
   director_override:$("p004-override").value,
   simulation_only:true,source_status:"HYPOTHETICAL"};
  const result=await call("plan",request);
  token=result.token;valid=false;sessionStorage.setItem("p004_five_skill_token",token);
  $("p004-review").disabled=false;$("p004-copy").disabled=false;$("p004-adopt").disabled=true;
  $("p004-prompt").value=result.prompt;$("p004-json").value="";$("p004-preview").replaceChildren();
  $("p004-cast").textContent="本场导演选中 "+result.cast_count+" 名候选人物："+result.task.cast.map(x=>x.speaker_id+" "+x.name).join("、")+"。允许沉默，不强制所有人发言。";
  stage("选角完成 · 等待编剧");
  feedback("选角程序真实运行成功；尚未调用AI，尚无对白，正式历史未改变。");
 }catch(e){stage("选角失败");feedback(e.message)}
};
$("p004-copy").onclick=async()=>{try{await navigator.clipboard.writeText($("p004-prompt").value);feedback("完整编剧任务已复制；可交给现有ChatGPT生成JSON。")}
catch(e){feedback("复制失败，请手动选中提示词复制："+e.message)}};
$("p004-copy-json").onclick=async()=>{try{await navigator.clipboard.writeText($("p004-json").value);feedback("已复制当前剧本JSON")}
catch(e){feedback("复制失败："+e.message)}};
$("p004-review").onclick=async()=>{
 try{
  const manuscript=JSON.parse($("p004-json").value);
  const result=await call("review",{token,manuscript});
  const q=result.report;valid=q.blocking_issues.length===0;
  $("p004-adopt").disabled=!valid||approved!==65;
  $("p004-preview").replaceChildren();
  (Array.isArray(manuscript.messages)?manuscript.messages:[]).forEach(m=>{
   const p=document.createElement("div");p.className="p004-speech";
   const strong=document.createElement("strong");strong.textContent=m.speaker_id+" / "+m.message_id+"　";
   const span=document.createElement("span");span.textContent=m.text;p.append(strong,span);
   $("p004-preview").append(p);
  });
  stage(valid?"结构通过 · 待编辑":"退稿修改");
  feedback(valid?"结构校验通过；仍需人工检查真实性、罗马尼亚语及文学效果。\n"+q.warnings.join("\n"):"退稿理由：\n"+q.blocking_issues.join("\n"));
 }catch(e){valid=false;$("p004-adopt").disabled=true;feedback("校验失败："+e.message)}
};
$("p004-adopt").onclick=async()=>{
 try{
  const x=await call("adopt",{token,editorial_confirmed:$("p004-editor").checked,
        operator_confirmed:$("p004-operator").checked});
  stage("正式采用");feedback("已写入独立历史（未公开发布）："+JSON.stringify(x.adoption));
  valid=false;$("p004-adopt").disabled=true;
 }catch(e){feedback("正式采用被阻止："+e.message)}
};

let reviewedPeople=[];
function showPerson(){
 const id=$("p004-person-select").value;
 const p=reviewedPeople.find(x=>x.id===id);
 $("p004-person-reviewed").checked=false;
 $("p004-person-confirmed").checked=false;
 $("p004-approve-person").disabled=!p||p.approved;
 if(!p){$("p004-profile").textContent="请选择人物查看完整审阅字段。";return;}
 $("p004-profile").textContent=JSON.stringify({
  编号:p.id,姓名:p.name,性别:p.gender,年龄:p.age,地区:p.region,职业:p.occupation,
  家庭动机:p.family_motivation,主性格:p.main_behavior,次性格:p.secondary_behavior,
  语言风格:p.voice,出场习惯:p.availability_note,
  状态:p.approved?"已人工批准":"新候选，未批准"
 },null,2);
}
async function loadPeople(){
 const r=await fetch("/api/p004/characters",{credentials:"same-origin"});
 const data=await r.json();if(!r.ok)throw Error(data.error||"候选人物读取失败");
 reviewedPeople=data.people;
 const select=$("p004-person-select"),old=select.value;
 select.replaceChildren();
 for(const p of data.people){
  const opt=document.createElement("option");opt.value=p.id;
  opt.textContent=p.id+" · "+p.name+(p.approved?" [已批准]":" [待审核]");
  select.append(opt);
 }
 if(data.people.some(x=>x.id===old))select.value=old;
 $("p004-approved-count").textContent=data.approved_count+" / 65 正式批准";
 showPerson();
}
$("p004-person-select").addEventListener("change",showPerson);
$("p004-approve-person").onclick=async()=>{
 const p=reviewedPeople.find(x=>x.id===$("p004-person-select").value);
 if(!p)return;
 try{
  const result=await call("approve-character",{
   id:p.id,confirmed_name:p.name,
   reviewed:$("p004-person-reviewed").checked,
   confirmed:$("p004-person-confirmed").checked});
  feedback("已真正批准新人物 "+p.id+" "+p.name+"。正式人数："+result.approved_count+"/65；无自动群发。");
  await loadPeople();await getStatus();
 }catch(e){feedback("批准失败："+e.message)}
};
loadPeople().catch(e=>feedback("人物清单无法读取："+e.message));

getStatus().catch(e=>{stage("数据异常");feedback(e.message)});
const remembered=sessionStorage.getItem("p004_five_skill_token");
if(remembered){
 call("restore",{token:remembered}).then(x=>{
  token=remembered;$("p004-prompt").value=x.prepared.llm_prompt;
  $("p004-cast").textContent="已恢复场次："+x.prepared.task.scene_id;
  $("p004-copy").disabled=false;$("p004-review").disabled=x.adopted;
  if(x.manuscript){$("p004-json").value=JSON.stringify(x.manuscript,null,2);}
  valid=!!(x.report&&x.report.status==="EDITORIAL_REVIEW_REQUIRED"&&!x.adopted);
  $("p004-adopt").disabled=!valid||approved!==65;
  stage(x.adopted?"已采用":"已恢复草稿");
 }).catch(()=>sessionStorage.removeItem("p004_five_skill_token"));
}
})();
</script>
"""
def embed(page):
    marker = '<div class="app">'
    if marker not in page or '</body>' not in page:
        raise ValueError("The existing Skill page structure changed")
    return page.replace(marker,marker + PANEL,1).replace("</body>",SCRIPT + "</body>",1)
