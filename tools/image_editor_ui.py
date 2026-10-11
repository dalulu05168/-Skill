"""Client-side image editor for module four; no remote uploads or simulated results."""
PAGE = r'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>图片编辑 · NUVEXA FINANCE</title>
<style>
*{box-sizing:border-box}
:root{color-scheme:light;font-family:Inter,"Microsoft YaHei",system-ui,sans-serif;color:#1d2939;background:#f5f6f8}
html,body{height:100%;margin:0;overflow:hidden}
body{display:grid;place-items:center;background:linear-gradient(135deg,#fff,#f1f3f6)}
.shell{width:min(calc(100vw - 20px),calc((100dvh - 20px) * 16/9),1680px);aspect-ratio:16/9;max-height:calc(100dvh - 20px);display:grid;
grid-template-columns:82px minmax(0,1fr);grid-template-rows:66px minmax(0,1fr);overflow:hidden;border:1px solid #dfe5ed;border-radius:16px;
background:#fff;box-shadow:0 18px 60px #172b420f}
.rail{grid-area:1/1/3/2;border-right:1px solid #e7ebef;padding:15px 5px;display:flex;flex-direction:column;gap:12px;background:#fcfcfd}
.brand{font-size:21px;font-weight:900;letter-spacing:-.08em;text-align:center;color:#263748;margin-bottom:8px;text-decoration:none}
.nav{display:flex;flex-direction:column;gap:9px}
.nav a{display:grid;justify-items:center;gap:5px;text-decoration:none;color:#637184;font-size:11px;border-radius:10px;padding:11px 2px;font-weight:650}
.nav a[aria-current=page],.nav a:hover{background:#ecf2f7;color:#284869}
.nav b{font-size:21px;line-height:1}
.topbar{grid-area:1/2/2/3;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 24px;border-bottom:1px solid #e8edf2}
.topbar strong{font-size:18px;letter-spacing:.01em}.topbar small{display:block;color:#8792a1;font-size:11px;margin-top:3px}
.pill{font-size:11px;color:#47637d;border:1px solid #dce5ec;border-radius:22px;padding:7px 11px;background:#f8fafb}
.editor{grid-area:2/2/3/3;min-height:0;display:grid;grid-template-columns:minmax(0,1fr) 300px}
.work{min-width:0;min-height:0;display:flex;flex-direction:column;gap:12px;justify-content:center;padding:clamp(12px,2vw,28px);background:#f6f8fa}
.workhead{display:flex;justify-content:space-between;gap:8px;align-items:center;font-size:12px;color:#667587}
.workhead b{font-size:14px;color:#344356}
.canvas-frame{flex:0 1 auto;aspect-ratio:16/9;width:100%;border:8px solid #fff;border-radius:12px;overflow:hidden;box-shadow:0 13px 40px #0d1c2c1c;background:#fff;display:grid;place-items:center}
canvas{display:block;width:100%;height:100%;touch-action:none;cursor:grab}
.canvas-frame:active canvas{cursor:grabbing}
.workfoot{font-size:11px;color:#788596;display:flex;justify-content:space-between;gap:12px;align-items:center}
.inspector{min-height:0;display:flex;flex-direction:column;gap:14px;padding:20px 20px 18px;border-left:1px solid #e9edf1;background:#fff;overflow:auto;scrollbar-width:none}
.inspector::-webkit-scrollbar{display:none}
.inspector h2{font-size:16px;margin:0}.hint{font-size:11px;line-height:1.7;color:#7c8997;margin:0}
.field{display:grid;gap:7px;color:#445365;font-size:12px;font-weight:700}
.field textarea,.field select,.field input:not([type=color]):not([type=range]):not([type=file]){width:100%;border:1px solid #dce3eb;background:#fafbfc;border-radius:8px;color:#233247;font:inherit;padding:10px}
.field textarea{resize:none;height:66px}
.field input[type=range]{width:100%;accent-color:#637f9f}
.field input[type=color]{width:100%;height:35px;border:1px solid #dce3eb;border-radius:8px;background:#fff;padding:3px;cursor:pointer}
.field input[type=file]{width:100%;font-size:11px;color:#566577}
.columns{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.rule{height:1px;background:#ebeff2;margin:0}
.actions{margin-top:auto;display:flex;gap:9px}
button{appearance:none;cursor:pointer;border:1px solid #d8e2ea;background:#fff;color:#34506a;border-radius:9px;font-size:12px;font-weight:750;padding:11px 12px}
button:hover{background:#edf3f8}
button.primary{background:#304d68;border-color:#304d68;color:#fff;flex:1}
button.primary:hover{background:#203f5b}
button:focus-visible,a:focus-visible,input:focus-visible,textarea:focus-visible,select:focus-visible{outline:2px solid #658bb4;outline-offset:2px}
.status{min-height:18px;color:#456d59;font-size:11px}
@media(max-width:1080px){.editor{grid-template-columns:minmax(0,1fr) 230px}.inspector{padding:13px;gap:10px}.work{padding:12px;gap:8px}}
@media(max-width:700px){html,body{overflow:hidden}.shell{height:100dvh;max-height:none;width:100%;aspect-ratio:auto;border:0;border-radius:0;grid-template-columns:53px minmax(0,1fr);grid-template-rows:56px minmax(0,1fr)}
.rail{padding:10px 2px}.brand{font-size:17px}.nav a{font-size:9px}.nav b{font-size:17px}
.topbar{padding:8px 12px}.topbar strong{font-size:14px}.pill{display:none}
.editor{grid-template-columns:1fr;grid-template-rows:minmax(0,1fr) minmax(260px,.9fr)}
.work{padding:12px}.inspector{border-left:0;border-top:1px solid #e9edf1;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;overflow:auto}
.inspector h2,.inspector .hint,.inspector .rule,.inspector .status{grid-column:1/-1}.inspector .actions{grid-column:1/-1;margin-top:0}
.field textarea{height:48px}.workfoot{font-size:9px}.canvas-frame{border-width:4px}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
</style></head>
<body>
<div class="shell">
<aside class="rail" aria-label="模块导航">
<a class="brand" href="/" aria-label="返回总入口">NX</a>
<nav class="nav">
<a href="/"><b>▦</b>总入口</a>
<a href="/news/"><b>▤</b>新闻</a>
<a href="/trading/"><b>▥</b>交易</a>
<a href="/skill/"><b>✦</b>Skill</a>
<a href="/image-editor/" aria-current="page"><b>▧</b>图片</a>
</nav></aside>
<header class="topbar"><div><strong>图片编辑工作台</strong><small>模块 04 / 图片工具 / 16:9 画布</small></div><span class="pill">本地编辑 · 不上传素材</span></header>
<main class="editor">
<section class="work" aria-label="图片预览">
<div class="workhead"><b>预览画布</b><span id="resolution">16:9 · 输出 3840 × 2160</span></div>
<div class="canvas-frame"><canvas id="stage" width="1920" height="1080" aria-label="编辑画布，可拖动标题位置"></canvas></div>
<div class="workfoot"><span>拖动标题可调整位置</span><span>无行情模拟 · 无服务器上传</span></div>
</section>
<aside class="inspector" aria-label="编辑工具">
<h2>图片编辑</h2><p class="hint">上传本地素材，编辑文字和颜色，导出真实 4K PNG。</p>
<label class="field">本地图片<input id="photo" type="file" accept="image/*"></label>
<label class="field">文字内容<textarea id="caption" maxlength="100">在此输入标题</textarea></label>
<div class="columns"><label class="field">文字颜色<input id="color" type="color" value="#22334a"></label>
<label class="field">字号<input id="font" type="range" min="36" max="155" value="84"></label></div>
<div class="columns"><label class="field">亮度<input id="brightness" type="range" min="40" max="160" value="100"></label>
<label class="field">适配<input id="fit" type="select"><option value="cover">填充</option><option value="contain">完整显示</option></select></label></div>
<div class="rule"></div>
<div class="actions"><button id="reset" type="button">重置</button><button id="export" type="button" class="primary">导出 4K PNG ↓</button></div>
<div class="status" role="status" id="status" aria-live="polite">准备就绪 · 图片仅在本机处理</div>
</aside>
</main></div>
<script>
(()=>{"use strict";
const $=id=>document.getElementById(id), canvas=$("stage"), ctx=canvas.getContext("2d");
const state={image:null,text:"在此输入标题",color:"#22334a",font:84,brightness:100,fit:"cover",x:.5,y:.53,drag:false};
const draw=(context,w,h)=>{
 const scale=w/1920;context.save();context.clearRect(0,0,w,h);
 const grad=context.createLinearGradient(0,0,w,h);
 grad.addColorStop(0,"#f9fafb");grad.addColorStop(1,"#e8edf3");context.fillStyle=grad;context.fillRect(0,0,w,h);
 if(state.image){const img=state.image;const ratio=state.fit==="cover"?Math.max(w/img.width,h/img.height):Math.min(w/img.width,h/img.height);
 const dw=img.width*ratio,dh=img.height*ratio;
 context.filter="brightness("+state.brightness+"%)";
 context.drawImage(img,(w-dw)/2,(h-dh)/2,dw,dh);context.filter="none";}
 const lines=state.text.split(/\n/).slice(0,5);
 context.textAlign="center";context.textBaseline="middle";context.font="700 "+(state.font*scale)+"px system-ui, Microsoft YaHei, sans-serif";context.fillStyle=state.color;
 const height=state.font*scale*1.28;
 const top=state.y*h-(lines.length-1)*height/2;
 for(let i=0;i<lines.length;i++){let line=lines[i].slice(0,50);context.fillText(line,state.x*w,top+i*height,w*.9);}
 context.restore();
};
const repaint=()=>draw(ctx,canvas.width,canvas.height);
["caption","color","font","brightness","fit"].forEach(id=>$(id).addEventListener("input",e=>{
 const v=e.target.value;state[id==="caption"?"text":id]=id==="font"||id==="brightness"?Number(v):v;repaint();
}));
$("photo").addEventListener("change",e=>{
 const file=e.target.files?.[0];if(!file)return;
 if(!file.type.startsWith("image/")){$("status").textContent="请选择图片格式";return;}
 const url=URL.createObjectURL(file), img=new Image();
 img.onload=()=>{state.image=img;URL.revokeObjectURL(url);$("status").textContent="素材已载入，未上传到服务器";repaint();};
 img.onerror=()=>{URL.revokeObjectURL(url);$("status").textContent="图片无法读取，请换一张";};
 img.src=url;
});
function position(e){const r=canvas.getBoundingClientRect();return {x:(e.clientX-r.left)/r.width,y:(e.clientY-r.top)/r.height};}
canvas.addEventListener("pointerdown",e=>{state.drag=true;canvas.setPointerCapture(e.pointerId);const p=position(e);state.x=Math.max(.06,Math.min(.94,p.x));state.y=Math.max(.06,Math.min(.94,p.y));repaint();});
canvas.addEventListener("pointermove",e=>{if(!state.drag)return;const p=position(e);state.x=Math.max(.06,Math.min(.94,p.x));state.y=Math.max(.06,Math.min(.94,p.y));repaint();});
canvas.addEventListener("pointerup",()=>state.drag=false);
canvas.addEventListener("pointercancel",()=>state.drag=false);
$("reset").addEventListener("click",()=>{
 state.image=null;state.text="在此输入标题";state.color="#22334a";state.font=84;state.brightness=100;state.fit="cover";state.x=.5;state.y=.53;
 ["caption","color","font","brightness","fit"].forEach(id=>$(id).value=state[id==="caption"?"text":id]);
 $("photo").value="";$("status").textContent="已重置";repaint();
});
$("export").addEventListener("click",()=>{
 const out=document.createElement("canvas");out.width=3840;out.height=2160;
 const context=out.getContext("2d");if(!context){$("status").textContent="浏览器无法创建画布";return;}
 draw(context,out.width,out.height);out.toBlob(blob=>{
 if(!blob){$("status").textContent="导出失败";return;}
 const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download="nuvexa-image-4k.png";a.click();
 setTimeout(()=>URL.revokeObjectURL(url),30000);$("status").textContent="4K PNG 已导出（3840 × 2160）";
 },"image/png");
});
repaint();
})();
</script></body></html>'''
