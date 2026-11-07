"""Headless adapter; never creates a Tk window or starts a scheduler."""
import sys, os, json, base64, io, zipfile, re
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
DATA=Path(os.environ['EW_TOOL_DATA']);DATA.mkdir(parents=True,exist_ok=True)
request=json.load(sys.stdin);action=request.get('action');key=request.get('market','RO')
theme=request.get('theme','graphite')
if theme not in ('flow','glass','graphite'):raise ValueError('开盘只允许FLOW、GLASS、GRAPHITE三套主题')
if action=='qa-export':
    theme=request.get('theme','flow')
    if theme not in ('flow','glass','graphite'): raise ValueError('问答主题无效')
    texts=request['texts']
    if not isinstance(texts,list) or len(texts)!=4 or any(not isinstance(s,str) or len(s)>12000 for s in texts):raise ValueError('问答内容无效')
    if any(re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]',value) for value in texts):raise ValueError('包含PPTX不支持的控制字符，请删除后导出')
    sizes=request.get('fontSizes')
    if sizes is not None and (not isinstance(sizes,list) or len(sizes)!=len(texts) or any(not isinstance(v,(int,float)) or not 20<=v<=80 for v in sizes)):raise ValueError('字号无效')
    layout=request.get('layout')
    if layout is not None:
        if not isinstance(layout,list) or not 1<=len(layout)<=30:raise ValueError('排版数据无效')
        for op in layout:
            if not isinstance(op,dict) or not isinstance(op.get('lines'),list) or any(not isinstance(t,str) or len(t)>12000 or re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]',t) for t in op['lines']):raise ValueError('排版文字无效')
            for key in ['x','y','w','h','size','lineHeight']:
                if not isinstance(op.get(key),(int,float)) or not 0<=op[key]<=2160:raise ValueError('排版尺寸无效')
            if not 12<=op['size']<=100 or op.get('weight') not in [400,700] or not re.fullmatch(r'#[0-9a-fA-F]{6}',op.get('color','')):raise ValueError('排版样式无效')
    brand_bytes=None
    theme_bg=(ROOT/'assets'/f'qa-background-{theme}.png').read_bytes()
    # Selected QA theme backgrounds already contain the approved logo,
    # so do not inject a second logo into the PPT export.
    out=io.BytesIO()
    with zipfile.ZipFile(ROOT/'qa-template.pptx') as src,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            b=src.read(info.filename)
            if info.filename=='ppt/slides/_rels/slide1.xml.rels' and brand_bytes is not None:
                b=b.replace(b'</Relationships>',b'<Relationship Id="rIdOriginalBrand" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/original-brand.png"/></Relationships>')
            if info.filename=='ppt/media/qa-background.png':
                b=theme_bg
            if info.filename=='ppt/slides/slide1.xml':
                from xml.sax.saxutils import escape
                model=json.loads((ROOT/'qa-model.json').read_text(encoding='utf-8'))
                shape_ids=[str(item['id']) for item in model['texts']]
                xml=b.decode('utf-8');seen=[]
                def replace_shape(match):
                    shape=match.group(0)
                    identity=re.search(r'<p:cNvPr\b[^>]*\bid="(\d+)"',shape)
                    if not identity or identity.group(1) not in shape_ids:return shape
                    index=shape_ids.index(identity.group(1));seen.append(index)
                    count=[0]
                    def replace_run(run):
                        value=escape(texts[index]) if count[0]==0 else ''
                        count[0]+=1
                        return '<a:t xml:space="preserve">'+value+'</a:t>'
                    if sizes is not None:
                        emu_width=15925800
                        size=round(sizes[index]*emu_width/1920/12700*100)
                        shape=re.sub(r'(<a:(?:rPr|endParaRPr)\b[^>]*\bsz=")\d+(")',lambda m:m.group(1)+str(size)+m.group(2),shape)
                    return re.sub(r'<a:t(?:\s[^>]*)?>.*?</a:t>',replace_run,shape,flags=re.S)
                xml=re.sub(r'<p:sp>.*?</p:sp>',replace_shape,xml,flags=re.S)
                if sorted(seen)!=list(range(len(texts))):raise ValueError('模板文字结构发生变化，未导出')
                if layout is not None:
                    from xml.sax.saxutils import escape
                    shapes=[];scale=15925800/1920;shape_id=100
                    for op in layout:
                        y=op['y']
                        for line in op['lines']:
                            if line:
                                shape_id+=1;size=round(op['size']*scale/127)
                                shapes.append(f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="Editable text {shape_id}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{round(op["x"]*scale)}" y="{round(y*scale)}"/><a:ext cx="{round(op["w"]*scale)}" cy="{round(op["lineHeight"]*scale)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap="none" lIns="0" rIns="0" tIns="0" bIns="0"><a:noAutofit/></a:bodyPr><a:lstStyle/><a:p><a:pPr/><a:r><a:rPr lang="ro-RO" sz="{size}" b="{1 if op["weight"]==700 else 0}"><a:solidFill><a:srgbClr val="{op["color"][1:]}"/></a:solidFill><a:latin typeface="Arial"/></a:rPr><a:t xml:space="preserve">{escape(line)}</a:t></a:r></a:p></p:txBody></p:sp>')
                            y+=op['lineHeight']*(1 if line else .45)
                    xml=re.sub(r'<p:sp>.*?</p:sp>','',xml,flags=re.S).replace('</p:spTree>',''.join(shapes)+'</p:spTree>')
                if brand_bytes is not None:
                    scale=15925800/1920
                    picture=f'<p:pic><p:nvPicPr><p:cNvPr id="900" name="Original brand logo"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="rIdOriginalBrand"/><a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr><a:xfrm><a:off x="{round(60*scale)}" y="{round(40*scale)}"/><a:ext cx="{round(250*scale)}" cy="{round(250*533/1000*scale)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>'
                    xml=xml.replace('</p:spTree>',picture+'</p:spTree>')
                b=xml.encode('utf-8')
            dst.writestr(info,b)
        if brand_bytes is not None:dst.writestr('ppt/media/original-brand.png',brand_bytes)
    result={'file':base64.b64encode(out.getvalue()).decode(),'name':f'问答模板_{theme.upper()}_已编辑.pptx','mime':'application/vnd.openxmlformats-officedocument.presentationml.presentation'}
else:
    sys.path.insert(0,str(ROOT.parent/'market'))
    import market_data as feed,rendering,intraday
    import application as original
    original.DATA_DIR=DATA;original.EXPORTS=DATA/'exports';original.ensure_dirs()
    if key not in feed.MARKETS:raise ValueError('未知市场')
    cache=DATA/(key+'.json')
    if action=='preview':
        # Selection only: never reuse old quotes or fetch market data.
        data=rendering.empty_data(key)
    elif action=='refresh':
        data=feed.fetch_market(key,request.get('provider','hybrid'))
        cache.write_text(json.dumps(data,default=lambda v:v.isoformat(),ensure_ascii=False))
    elif cache.exists():
        data=json.loads(cache.read_text())
        for quote in data.values():
            if quote.get('timestamp'):quote['timestamp']=datetime.fromisoformat(quote['timestamp'])
            if quote.get('provider')=='yahoo' and quote.get('reference_version')!=2:
                quote.pop('timestamp',None)
                quote.update(last=None,prev=None,pct=None,status='NA',reason='请重新获取行情')
        feed.refresh(key,data)
    else:data=rendering.empty_data(key)
    if action=='send':original.telegram(key,data,theme=theme)
    image=io.BytesIO();rendering.render(key,data,3840 if action=='export' else 1920,theme=theme).save(image,'PNG')
    rows=[]
    for item in feed.MARKETS[key]['items']:
        q=data.get(item[0],{})
        rows.append({'label':item[0],'symbol':item[1],**q,
                     'chart_ready':bool(intraday.chart_points(q,symbol=item[1]))})
    result={'rows':rows,'image':base64.b64encode(image.getvalue()).decode(),'caption':rendering.caption(key,data),'publishable':feed.publishable(key,data),'sent':action=='send'}
    if action=='export':result.update(file=result['image'],name=f'{key}_{feed.now_for(key).strftime("%Y%m%d_%H%M%S")}_4K'+('' if feed.publishable(key,data) else '_NOT_VERIFIED')+'.png',mime='image/png')
print(json.dumps(result,ensure_ascii=False,default=lambda v:v.isoformat()))