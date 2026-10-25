"""Approved 2026-10-24 Canva FLOW/GLASS/GRAPHITE market artworks.

RO empty-state panels use the exact approved slide raster. Data-bearing cards
are redrawn at the same Canva coordinates over the original building artwork;
only real validated quote values and independently checked intraday points
may replace the placeholders. US artwork uses those same three approved visual
systems with US symbols, rather than leaking Romanian labels into US market.

Rendering is 3840x2160 throughout; smaller previews are downsampled from the
same output so preview and PNG export cannot silently diverge.
"""
from pathlib import Path
from functools import lru_cache
import math
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent/'assets'
W,H=3840,2160
RISE_GREEN=(69,233,135)
FALL_RED=(255,95,109)

def signed_change(percent):
    """Explicit + for rising, minus for falling; no +0.00/-0.00 confusion."""
    pct=round(float(percent),2)
    return f'{pct:+.2f}%' if pct else '0.00%'

def change_ink(percent):
    return RISE_GREEN if round(float(percent),2)>0 else FALL_RED if round(float(percent),2)<0 else (219,230,240)

LOGO_RECT=(144,92,470,251)  # same original brand asset on all three Canva pages
TITLE_RECT=(2650,140,1000,82)
CARD_X=(140,1354,2568)
CARD_Y=482
CARD_W,CARD_H=1132,1200
FOOT_X=144
FOOT_Y=1807
FOOT_TOTAL=3550
FOOT_GAP=33
T={
 'flow':{'fill':(10,29,52),'edge':(92,154,207),'footer':(36,81,124),'text':(233,241,248)},
 'glass':{'fill':(21,46,67),'edge':(152,196,220),'footer':(53,98,126),'text':(233,241,248)},
 'graphite':{'fill':(28,35,44),'edge':(143,159,176),'footer':(76,91,110),'text':(233,241,248)},
}

@lru_cache(maxsize=32)
def _font(sz,bold=False):
    paths=['C:/Windows/Fonts/arialbd.ttf','DejaVuSans-Bold.ttf'] if bold else ['C:/Windows/Fonts/arial.ttf','DejaVuSans.ttf']
    for path in paths:
        try: return ImageFont.truetype(path,sz)
        except OSError: pass
    return ImageFont.load_default()

@lru_cache(maxsize=7)
def _raster(path):
    with Image.open(ROOT/path) as im:
        if im.size!=(W,H):raise ValueError(f'Approved Canva source is not 3840x2160: {path}')
        return im.convert('RGBA')

def _valid(quote):
    if quote.get('status') not in ('OK','CLOSED'):return False
    return all(isinstance(quote.get(k),(float,int)) and not isinstance(quote.get(k),bool)
               and math.isfinite(quote[k]) for k in ('last','pct'))

def _rect(layer,box,color,opacity,radius=18,border=None,linewidth=2):
    dr=ImageDraw.Draw(layer,'RGBA')
    dr.rounded_rectangle(box,radius=radius,fill=(*color,opacity),outline=(*border,180) if border else None,width=linewidth)

def _text(layer,s,x,y,sz,color,*,align='left',bold=False,max_width=None):
    d=ImageDraw.Draw(layer,'RGBA')
    f=_font(sz,bold)
    if max_width:
        while sz>21 and d.textlength(s,font=f)>max_width:
            sz-=1;f=_font(sz,bold)
    anchors={'left':'lt','center':'mt','right':'rt'}
    d.text((x,y),s,font=f,fill=(*color,255),anchor=anchors[align])

def _main_card(layer,theme,x,title,description,quote,decimals,symbol):
    cfg=T[theme]; fill,edge=cfg['fill'],cfg['edge'];light=cfg['text']
    _rect(layer,(x,CARD_Y,x+CARD_W,CARD_Y+CARD_H),fill,166,border=edge)
    _text(layer,title,x+62,CARD_Y+54,68,light,max_width=CARD_W-130)
    if _valid(quote):
        shown=f'{quote["last"]:,.{decimals}f}'
        change=signed_change(quote['pct'])
        change_color=change_ink(quote['pct'])
    else:shown,change,change_color='—','—%',light
    _text(layer,shown,x+62,CARD_Y+228,106,light,bold=True,max_width=CARD_W-130)
    _text(layer,'VARIAȚIE',x+62,CARD_Y+390,51,(213,223,236))
    _text(layer,change,x+495,CARD_Y+390,51,change_color,max_width=510)
    _rect(layer,(x+62,CARD_Y+510,x+CARD_W-62,CARD_Y+1020),fill,121,border=edge,radius=16)
    _text(layer,description,x+62,CARD_Y+1102,38,(222,233,243),max_width=CARD_W-122)
    # The canvas part of the chart is painted after card compositing.


def _footer(layer,theme,items):
    cfg=T[theme];names=list(items); n=len(names)
    gap=FOOT_GAP if n==5 else 52
    sw=(FOOT_TOTAL-gap*(n-1))/n
    for i,(code,q,decimals,unit) in enumerate(items):
        x=FOOT_X+i*(sw+gap)
        _rect(layer,(int(x),FOOT_Y,int(x+sw),2087),cfg['footer'],107,border=cfg['edge'],radius=22)
        _text(layer,code,int(x+sw/2),FOOT_Y+30,58,(239,245,253),align='center')
        value=(f'{q["last"]:,.{decimals}f}'+('%' if unit=='%' else '')) if _valid(q) else '—'
        change=signed_change(q['pct']) if _valid(q) else ''
        # Keep price neutral while signed performance uses a consistent green/red.
        _text(layer,value,int(x+sw/2),FOOT_Y+119,49,(219,230,240),align='center',max_width=sw-36)
        if change:
            _text(layer,change,int(x+sw/2),FOOT_Y+195,46,change_ink(q['pct']),align='center',max_width=sw-36)


def render(key,data,theme,width=1920):
    if key not in ('RO','US') or theme not in T or width not in (960,1920,3840):
        raise ValueError('Unsupported market/theme/size')
    import market_data as feed
    from chart_draw import draw_verified_chart
    rows=feed.MARKETS[key]['items']
    # Never manufacture a point, a price, or a provider; the verified feed
    # remains the only dynamic source.
    filled=any(_valid(data.get(name,{})) for name,*_ in rows)
    if not filled and key=='RO':
        base=_raster(f'canva_{theme}_approved_blank_4k.png').copy()
        if width!=W:base=base.resize((width,width*9//16),Image.Resampling.LANCZOS)
        return base.convert('RGB')

    base=_raster(f'canva_{theme}_background_4k.png').copy()
    lay=Image.new('RGBA',(W,H),(0,0,0,0))
    index_names=['BET','BET-NG','BET-FI'] if key=='RO' else ['DOW JONES','S&P 500','NASDAQ']
    descriptions=['MAIN EQUITY INDEX','ENERGY & UTILITIES','FINANCIAL INVESTMENT INDEX'] if key=='RO' else ['DOW JONES INDUSTRIAL','LARGE-CAP INDEX','NASDAQ COMPOSITE']
    for i,(name,symbol,decimals,unit,provider) in enumerate(rows[:3]):
        _main_card(lay,theme,CARD_X[i],index_names[i],descriptions[i],data.get(name,{}),decimals,symbol)
    _text(lay,'WATCHLIST',144,1718,42,(224,234,245))
    if key=='RO':
        footer_items=[(code,data.get(row[0],{}),row[2],row[3]) for code,row in zip(['TLV','BRD','H2O','SNP','SNG'],rows[3:])]
    else:
        footer_items=[(code,data.get(row[0],{}),row[2],row[3]) for code,row in zip(['US 10Y','GOLD','BRENT'],rows[3:])]
    _footer(lay,theme,footer_items)
    base=Image.alpha_composite(base,lay)
    # Three independently validated observed series; no old baked 'INTRADAY'
    # placeholder is present in the dynamic graphic area.
    for i,(name,symbol,*_) in enumerate(rows[:3]):
        quote=data.get(name,{})
        chart_x=CARD_X[i]+62; top=CARD_Y+510
        plot=(chart_x+5,top+5,CARD_X[i]+CARD_W-67,CARD_Y+1015)
        overlay=Image.new('RGBA',(W,H),(0,0,0,0))
        if _valid(quote) and draw_verified_chart(overlay,plot,quote,symbol=symbol,theme=theme,scale=2):
            base=Image.alpha_composite(base,overlay)
        else:
            _text(base,'—',CARD_X[i]+CARD_W//2,top+165,69,(198,216,229),align='center')
            _text(base,'INTRADAY',CARD_X[i]+CARD_W//2,top+312,39,(205,218,229),align='center')
    logo=Image.open(ROOT/'canva_brand_logo_original.png').convert('RGBA')
    logo=logo.resize((LOGO_RECT[2],LOGO_RECT[3]),Image.Resampling.LANCZOS)
    base.alpha_composite(logo,LOGO_RECT[:2])
    _text(base,'ROMANIA MARKET OPEN' if key=='RO' else 'US MARKET OPEN',TITLE_RECT[0]+TITLE_RECT[2],TITLE_RECT[1],56,(232,237,245),align='right')
    if width!=W:base=base.resize((width,width*9//16),Image.Resampling.LANCZOS)
    return base.convert('RGB')