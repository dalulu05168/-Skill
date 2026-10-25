"""Paint only verified minute observations inside the selected market template.

The palette belongs to the template, not to the market provider. Switching themes
never changes a single market observation and never manufactures an observation.
"""
from datetime import datetime
import math
from PIL import ImageDraw, ImageFont


CHART_THEMES = {
    # DEFAULT retains the previous neutral dark chart styling.
    'default': {
        'background': (5, 12, 23, 226), 'border': (119, 193, 243, 134),
        'line': (119, 193, 243, 255), 'halo': (2, 13, 30, 255),
        'grid': (192, 204, 222, 32), 'label': (214, 230, 241, 235),
    },
    'flow': {
        'background': (3, 21, 48, 250), 'border': (53, 142, 210, 180),
        'line': (101, 211, 255, 255), 'halo': (10, 70, 109, 255),
        'grid': (128, 179, 211, 38), 'label': (208, 237, 254, 245),
    },
    'glass': {
        'background': (20, 45, 64, 236), 'border': (154, 204, 227, 175),
        'line': (194, 243, 255, 255), 'halo': (28, 93, 120, 255),
        'grid': (198, 230, 243, 35), 'label': (230, 246, 251, 250),
    },
    'graphite': {
        'background': (17, 23, 31, 255), 'border': (142, 160, 178, 180),
        'line': (168, 228, 248, 255), 'halo': (65, 94, 112, 255),
        'grid': (188, 196, 202, 30), 'label': (231, 238, 242, 247),
    },
}


def _font(size):
    for path in ('DejaVuSans.ttf', 'C:/Windows/Fonts/arial.ttf'):
        try:
            return ImageFont.truetype(path, max(8, size))
        except OSError:
            pass
    return ImageFont.load_default()


def draw_verified_chart(image, box, quote, *, symbol, scale=1.0, theme='default', accent=None):
    """Returns False unless symbol/session/quote-consistent observations exist.

    Does not change quote data. Distinct themes change only chart ink and panel.
    """
    from intraday import chart_points
    rows = chart_points(quote, symbol=symbol)
    if len(rows) < 2:
        return False
    if theme not in CHART_THEMES:
        raise ValueError('Unknown chart theme')
    palette = CHART_THEMES[theme]
    # Direction is the verified change vs previous close, not the line's slope.
    # All three themes share the same semantic colours.
    pct = quote.get('pct')
    signed = round(float(pct),2) if isinstance(pct,(int,float)) and not isinstance(pct,bool) and math.isfinite(pct) else 0
    ink = (69,233,135,255) if signed>0 else (255,95,109,255) if signed<0 else (197,209,222,255)

    x0, y0, x1, y1 = (int(v) for v in box)
    if x1 - x0 < 80 or y1 - y0 < 80:
        raise ValueError('Invalid chart rectangle')
    dates = [datetime.fromisoformat(p['time']).timestamp() for p in rows]
    values = [float(p['price']) for p in rows]
    first, last = dates[0], dates[-1]
    if first >= last or any(not math.isfinite(v) for v in values):
        return False
    low, high = min(values), max(values)
    padding = (high-low) * .15 if high > low else max(high*.001, 1e-6)
    lo, hi = low-padding, high+padding
    left, right = x0 + 22*scale, x1 - 21*scale
    top, bottom = y0 + 38*scale, y1 - 47*scale
    if right <= left or bottom <= top:
        return False
    draw = ImageDraw.Draw(image, 'RGBA')
    draw.rounded_rectangle((x0, y0, x1, y1), radius=max(4, round(9*scale)),
                           fill=palette['background'], outline=palette['border'],
                           width=max(1, round(1.3*scale)))
    for j in range(1, 4):
        yy = round(top + (bottom-top)*j/4)
        draw.line(((left, yy), (right, yy)), fill=palette['grid'], width=max(1, round(scale)))
    pts = [(round(left+(t-first)/(last-first)*(right-left)),
            round(bottom-(v-lo)/(hi-lo)*(bottom-top))) for t,v in zip(dates, values)]
    # Two strokes: subdued outer accent keeps the price path identifiable when
    # displayed at preview scale; bright solid core retains crisp 4K output.
    draw.line(pts, fill=palette['halo'], width=max(4, round(6*scale)), joint='curve')
    draw.line(pts, fill=ink, width=max(3, round(3.1*scale)), joint='curve')
    radius=max(3,round(3.5*scale))
    for x,y in (pts[0],pts[-1]):
        draw.ellipse((x-radius,y-radius,x+radius,y+radius),
                     fill=ink, outline=palette['halo'],
                     width=max(1,round(scale)))
    ft = _font(round(12*scale))
    start_time = datetime.fromisoformat(rows[0]['time']).strftime('%H:%M')
    end_time = datetime.fromisoformat(rows[-1]['time']).strftime('%H:%M')
    provider = (quote.get('intraday') or {}).get('provider', '')
    draw.text((left,y0+7*scale),f'{provider} · {len(pts)} observations',
              font=ft,fill=palette['label'])
    draw.text((left,y1-31*scale),start_time,font=ft,fill=palette['label'])
    draw.text((right,y1-31*scale),end_time,font=ft,
              fill=palette['label'],anchor='ra')
    return True