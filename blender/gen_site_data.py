"""Generates src/data/site.json from the brochure's 'Typical Layout Plan' (page 8).

Coordinates: metres, x = East, y = North, origin = plot centre.
Real site: Vraj Platinum, Sarthana-Gadhpur Road, Surat (Google Maps pin 21.2318382 N, 72.9136999 E).
Compass on the layout: page-up = West, page-right = North, page-down = East (the 30 m road).
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 0.063          # metres per layout pixel (calibrated on Type A flat width 12.3 m)
OX, OY = 645, 752  # layout pixel of plot centre


def E(py):
    return round((py - OY) * S, 3)


def N(px):
    return round((px - OX) * S, 3)


def rect(px0, px1, py0, py1):
    """layout px rect -> [xmin, xmax, ymin, ymax] in (East, North) metres"""
    xs = sorted((E(py0), E(py1)))
    ys = sorted((N(px0), N(px1)))
    return [xs[0], xs[1], ys[0], ys[1]]


GROUND_H = 3.6
FLOOR_H = 3.0
FLOORS = 14

blocks = []

# square blocks (Type A flats)
def square(name, px0, px1, mirror):
    pyT0, pyT1, pyB0, pyB1 = 1045, 1157, 1206, 1318
    mid = (px0 + px1) / 2
    left, right = (px0, mid), (mid, px1)
    # A: top-left 103, top-right 104, bottom-left 102, bottom-right 101 ; B mirrored
    if not mirror:
        flats = [('103', left, (pyT0, pyT1)), ('104', right, (pyT0, pyT1)), ('102', left, (pyB0, pyB1)), ('101', right, (pyB0, pyB1))]
        outer = 'N'
    else:
        flats = [('104', left, (pyT0, pyT1)), ('103', right, (pyT0, pyT1)), ('101', left, (pyB0, pyB1)), ('102', right, (pyB0, pyB1))]
        outer = 'S'
    out = []
    for no, (a, b), (c, d) in flats:
        top = c == pyT0
        is_outer = (no in ('104', '101'))
        face = 'W' if top else 'E'
        views = [{'dir': face, 'label': 'Living & balcony'}]
        views.append({'dir': outer if is_outer else ('S' if outer == 'N' else 'N'), 'label': 'Bedroom side'})
        out.append(dict(no=no, type='A', rect=rect(a, b, c, d), face=face, views=views,
                        tag='Road facing' if face == 'E' else 'Garden & campus facing'))
    blocks.append(dict(id=name, kind='square', towers=[name], rect=rect(px0, px1, 1045, 1318),
                       core=rect(mid - 85, mid + 85, 1157, 1206), flats=out))


square('A', 737, 1148, False)
square('B', 145, 555, True)


def long_block(bid, towers, px0, px1, garden_side):
    """towers = (westTower, eastTower). Columns: left (south) & right (north)."""
    c = (px0 + px1) / 2
    lc, rc = (px0, c - 18.5), (c + 18.5, px1)
    rows = [(172, 365), (365, 540), (540, 720), (720, 912)]
    W, Et = towers
    if bid == 'DC':
        names = {(0, 'L'): (W, '101'), (0, 'R'): (W, '104'), (1, 'L'): (W, '102'), (1, 'R'): (W, '103'),
                 (2, 'L'): (Et, '102'), (2, 'R'): (Et, '103'), (3, 'L'): (Et, '101'), (3, 'R'): (Et, '104')}
    else:
        names = {(0, 'L'): (W, '104'), (0, 'R'): (W, '101'), (1, 'L'): (W, '103'), (1, 'R'): (W, '102'),
                 (2, 'L'): (Et, '103'), (2, 'R'): (Et, '102'), (3, 'L'): (Et, '104'), (3, 'R'): (Et, '101')}
    flats = []
    for ri, (a, b) in enumerate(rows):
        for side, (p0, p1) in (('L', lc), ('R', rc)):
            tw, no = names[(ri, side)]
            face = 'S' if side == 'L' else 'N'
            end = ri in (0, 3)
            typ = 'B' if end else 'C'
            views = [{'dir': face, 'label': 'Living room'}]
            if end:
                views.append({'dir': 'W' if ri == 0 else 'E', 'label': 'Bedroom balcony'})
            g = face == garden_side
            flats.append(dict(tower=tw, no=no, type=typ, rect=rect(p0, p1, a, b), face=face, views=views,
                              tag='Garden facing' if g else 'Open side facing'))
    blocks.append(dict(id=bid, kind='long', towers=list(towers), rect=rect(px0, px1, 172, 912),
                       core=rect(c - 18.5, c + 18.5, 260, 820), flats=flats))


long_block('DC', ('D', 'C'), 170, 462, 'N')
long_block('EF', ('E', 'F'), 832, 1125, 'S')

for b in blocks:
    for f in b['flats']:
        f.setdefault('tower', b['towers'][0])

site = dict(
    name='Vraj Platinum',
    geo=dict(lat=21.2318382, lng=72.9136999, originLat=21.2318382, originLng=72.913286, rotationDeg=0,
             note='Google Maps pin sits at the gate on the 100 ft road; the plot centre (model origin) is ~43 m west of it (verified on Esri imagery).'),
    groundH=GROUND_H, floorH=FLOOR_H, floors=FLOORS,
    plot=rect(50, 1240, 70, 1435),
    road=dict(rect=[E(1435), E(1435) + 30.0, N(-300), N(1650)], width=30.0, name='30.00 m wide road (Sarthana-Gadhpur 100 ft road)'),
    garden=rect(553, 740, 185, 900),
    playArea=rect(558, 735, 190, 280),
    waterBody=rect(580, 712, 893, 905),
    centralPlanter=rect(630, 660, 1055, 1305),
    gate=dict(x=E(1435), y=N(645), width=9.0),
    blocks=blocks,
    planterFloors=[3, 7, 11],
)
json.dump(site, open(os.path.join(ROOT, 'src', 'data', 'site.json'), 'w'), indent=1)
print('flats/floor', sum(len(b['flats']) for b in blocks), 'total', sum(len(b['flats']) for b in blocks) * FLOORS)
