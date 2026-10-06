"""Derive clean landcover polygons, road markings, tree and car positions (world metres)
from the near-nadir Esri mosaic (classes) and the sharper Bing mosaic (markings, trees).

  python site_vectors.py WORKDIR OUT.json      (WORKDIR from fetch_imagery.py + landcover.py)
Requires numpy and opencv-python.
"""
import cv2, numpy as np, json, math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'source', 'v2'))
import site_data as SD

K = SD.M_PER_PX
X0, Y0, X1, Y1 = 420, 300, 3584, 3060
OUT = os.path.abspath(sys.argv[2])
os.chdir(sys.argv[1])
cls = cv2.imread('landcover_raw.png', 0)[Y0:Y1, X0:X1].copy()
H, W = cls.shape
PARCEL_PX = [(564, 994), (2244, 467), (2328, 717), (2411, 994), (2522, 1217), (2661, 1439), (2800, 1633),
             (2939, 1800), (3036, 1939), (1105, 2744)]
WATERLINE_PX = [(2550, 0), (2703, 411), (2883, 856), (3078, 1217), (3300, 1550), (3578, 2022), (3800, 2420)]
LAGOON_HULL_PX = SD.LAGOON_RIM_PX

def img(pxpts):
    return np.array([(x - X0, y - Y0) for x, y in pxpts], np.int32)

def to_world(x, y):
    return [round((x + X0 - SD.ORIGIN_PX[0]) * K, 3), round(-(y + Y0 - SD.ORIGIN_PX[1]) * K, 3)]

parcel = np.zeros((H, W), np.uint8); cv2.fillPoly(parcel, [img(PARCEL_PX)], 1)
lagoon = np.zeros((H, W), np.uint8); cv2.fillPoly(lagoon, [img(LAGOON_HULL_PX)], 1)
# buildings
bmask = np.zeros((H, W), np.uint8)
def wimg(pts):
    return np.array([(x / K + SD.ORIGIN_PX[0] - X0, -y / K + SD.ORIGIN_PX[1] - Y0) for x, y in pts], np.int32)
for T in SD.TOWERS:
    ring = [SD.px(*p) for p in T['outer']] + [SD.px(*p) for p in reversed(T['inner'])]
    cv2.fillPoly(bmask, [wimg(ring)], 1)
for r in SD.VILLA_BLOCKS_ROT + [SD.BALLROOM_ROT] + SD.SERVICE_BLOCKS_ROT:
    x0, y0, x1, y1 = r
    cv2.fillPoly(bmask, [wimg([SD.rot(x0, y0), SD.rot(x1, y0), SD.rot(x1, y1), SD.rot(x0, y1)])], 1)
bmask = cv2.dilate(bmask, np.ones((7, 7), np.uint8))

lab = cls.copy()
lab[lab == 8] = 2
lab[(lab == 7) | (lab == 0)] = 0
lab[bmask > 0] = 2
# lagoon override: everything except vegetation is water inside the hull
lab[lagoon > 0] = 2                      # water park rim + water are modelled explicitly
for cxy, r in [(SD.WIND_SMALL_POOL_PX[0], SD.WIND_SMALL_POOL_PX[1] + 4)]:
    cv2.circle(lab, (int(cxy[0] - X0), int(cxy[1] - Y0)), int(r), 2, -1)
cv2.line(lab, (SD.WIND_POOL_PX[0][0] - X0, SD.WIND_POOL_PX[0][1] - Y0), (SD.WIND_POOL_PX[1][0] - X0, SD.WIND_POOL_PX[1][1] - Y0), 2, int(SD.WIND_POOL_PX[2] * 2 + 8))
# fill unknown from neighbours
for it in range(60):
    z = lab == 0
    if not z.any():
        break
    dil = cv2.dilate(lab, np.ones((3, 3), np.uint8))
    lab[z] = dil[z]
lab = cv2.medianBlur(lab, 5); lab = cv2.medianBlur(lab, 5)
# villa districts: paved pedestrian lanes between the shopvillas (tree crowns hide them on the aerial)
def rot_px(xr, yr):
    u, v = xr - 760.0, yr - 420.0
    a = math.radians(SD.PARCEL_ROT_DEG); c, s_ = math.cos(a), math.sin(a)
    return (c * u + s_ * v + SD.ORIGIN_PX[0] - X0, -s_ * u + c * v + SD.ORIGIN_PX[1] - Y0)
district = np.zeros((H, W), np.uint8)
for (a0, b0, a1, b1) in SD.VILLA_DISTRICTS_ROT:
    cv2.fillPoly(district, [np.array([rot_px(a0, b0), rot_px(a1, b0), rot_px(a1, b1), rot_px(a0, b1)], np.int32)], 1)
lab[(district > 0) & (lab != 1)] = 2
# sea side of the surveyed waterline is water, whatever the classifier said
seapoly = [(x - X0, y - Y0) for x, y in WATERLINE_PX] + [(X1 - X0 + 400, Y1 - Y0 + 400), (X1 - X0 + 400, -400), (WATERLINE_PX[0][0] - X0, -400)]
seamask = np.zeros((H, W), np.uint8); cv2.fillPoly(seamask, [np.array(seapoly, np.int32)], 1)
lab[seamask > 0] = 6
# outside parcel
out = parcel == 0
lab[out & (lab == 2)] = 4
lab[out & (lab == 3)] = 9      # scrub
lab[out & (lab == 5)] = 4
lab[out & (lab == 6) & (seamask == 0)] = 4
lab[(parcel > 0) & (lab == 6)] = 3     # dark-blue pixels inside the parcel are tower shadows
lab[(parcel > 0) & (lab == 4)] = 3     # sand patches inside resort read as planted beds -> lawn
# asphalt: keep only road-sized connected networks (tree shadows read as dark specks)
am = (lab == 1).astype(np.uint8)
n_, l_, st_, _ = cv2.connectedComponentsWithStats(am, connectivity=8)
for i in range(1, n_):
    area_m2 = st_[i][4] * K * K
    comp = l_ == i
    inside = parcel[comp].mean() > 0.5
    if (inside and area_m2 < 60) or ((not inside) and area_m2 < 600):
        lab[comp] = 3 if inside else 9

def polys_for(mask, min_area_m2, eps_px=0.9, blur=1.5, close=3):
    m = (mask > 0).astype(np.uint8) * 255
    if close:
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((close, close), np.uint8))
    up = cv2.resize(m, (W * 2, H * 2), interpolation=cv2.INTER_LINEAR)
    up = cv2.GaussianBlur(up, (0, 0), blur * 2)
    _, up = cv2.threshold(up, 127, 255, cv2.THRESH_BINARY)
    cnts, hier = cv2.findContours(up, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    res = []
    if hier is None:
        return res
    hier = hier[0]
    def simp(cc):
        cc = cv2.approxPolyDP(cc, eps_px * 2, True)[:, 0, :].astype(np.float64) / 2.0
        return [to_world(x, y) for x, y in cc]
    for i, c in enumerate(cnts):
        if hier[i][3] != -1:
            continue
        area = cv2.contourArea(c) / 4 * K * K
        if area < min_area_m2:
            continue
        outer = simp(c)
        holes = []
        ch = hier[i][2]
        while ch != -1:
            if cv2.contourArea(cnts[ch]) / 4 * K * K >= 6.0:
                hh = simp(cnts[ch])
                if len(hh) >= 3:
                    holes.append(hh)
            ch = hier[ch][0]
        if len(outer) >= 3:
            res.append(dict(outer=outer, holes=holes, area=round(area, 1)))
    return res

res = dict(
    asphalt=polys_for(lab == 1, 20.0, 1.0, 2.0, close=5),
    paving=polys_for(lab == 2, 25.0, 1.1, 2.2, close=5),
    lawn=polys_for(lab == 3, 25.0, 1.1, 2.2, close=5),
    scrub=polys_for(lab == 9, 30.0, 1.2, 2.0),
    pool=polys_for(lab == 5, 25.0, 0.6, 1.0),
    parcel=[to_world(x - X0, y - Y0) for x, y in PARCEL_PX],
    waterline=[[round((x - SD.ORIGIN_PX[0]) * K, 2), round(-(y - SD.ORIGIN_PX[1]) * K, 2)] for x, y in WATERLINE_PX],
)

# ---------------------------------------------------------------- road markings (Bing, sharper)
B = cv2.imread('mosaic19_bing.jpg')[Y0:Y1, X0:X1]
hsv = cv2.cvtColor(B, cv2.COLOR_BGR2HSV)
asph = cv2.erode(((lab == 1) * 255).astype(np.uint8), np.ones((5, 5), np.uint8))
white = ((hsv[..., 2] > 175) & (hsv[..., 1] < 45)).astype(np.uint8) * 255
yellow = ((hsv[..., 0] > 15) & (hsv[..., 0] < 35) & (hsv[..., 1] > 90) & (hsv[..., 2] > 150)).astype(np.uint8) * 255
marks = []
for colour, m in (("white", white), ("yellow", yellow)):
    m = cv2.bitwise_and(m, asph)
    n, labm, st, _ = cv2.connectedComponentsWithStats(m)
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < 3 or a > 400:
            continue
        ys, xs = np.where(labm[y:y + h, x:x + w] == i)
        pts = np.stack([xs + x, ys + y], 1).astype(np.float32)
        if len(pts) < 3:
            continue
        (cx, cy), (rw, rh), ang = cv2.minAreaRect(pts)
        L, Wd = max(rw, rh), min(rw, rh)
        if L < 3 or Wd > 3.5:
            continue
        if rw < rh:
            ang += 90
        a_r = math.radians(ang)
        dx, dy = math.cos(a_r) * L / 2, math.sin(a_r) * L / 2
        p0 = to_world(cx - dx, cy - dy); p1 = to_world(cx + dx, cy + dy)
        marks.append(dict(c=colour, p0=p0, p1=p1, w=round(max(0.12, min(0.3, Wd * K * 0.6)), 2)))
res['markings'] = marks

# ---------------------------------------------------------------- trees (Bing)
g = hsv.astype(np.int32)
tree = ((g[..., 0] >= 32) & (g[..., 0] <= 95) & (g[..., 1] > 55) & (g[..., 2] < 105)).astype(np.uint8) * 255
tree = cv2.morphologyEx(tree, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
tree[bmask > 0] = 0
dist = cv2.distanceTransform(tree, cv2.DIST_L2, 5)
mx = cv2.dilate(dist, np.ones((11, 11), np.uint8))
peaks = np.argwhere((dist == mx) & (dist >= 2.5))
trees = []
taken = np.zeros((H, W), np.uint8)
for y, x in sorted(peaks.tolist(), key=lambda p: -dist[p[0], p[1]]):
    if taken[y, x]:
        continue
    r = dist[y, x]
    cv2.circle(taken, (int(x), int(y)), int(max(6, r * 1.6)), 1, -1)
    inside = parcel[y, x] > 0
    c = int(lab[y, x])
    if c in (5, 6) or seamask[y, x]:
        continue
    trees.append([*to_world(x, y), round(float(r * K * 2.0), 2), 1 if inside else 0, c, int(district[y, x])])
res['trees'] = trees

# ---------------------------------------------------------------- vehicles on asphalt (Bing)
asph_full = ((lab == 1) * 255).astype(np.uint8)
asph_full = cv2.erode(asph_full, np.ones((3, 3), np.uint8))
bg = cv2.medianBlur(B, 21)
diff = cv2.absdiff(B, bg).sum(2)
vm = ((diff > 70) & (asph_full > 0)).astype(np.uint8) * 255
vm = cv2.morphologyEx(vm, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
n, lv, st, cen = cv2.connectedComponentsWithStats(vm)
cars = []
for i in range(1, n):
    a = st[i][4] * K * K
    if 4.0 <= a <= 14.0:
        ys, xs = np.where(lv == i)
        pts = np.stack([xs, ys], 1).astype(np.float32)
        (cx, cy), (rw, rh), ang = cv2.minAreaRect(pts)
        L, Wd = max(rw, rh) * K, min(rw, rh) * K
        if 3.2 <= L <= 6.0 and 1.3 <= Wd <= 2.6:
            if rw < rh:
                ang += 90
            col = B[int(cy), int(cx)].tolist()
            cars.append([*to_world(cx, cy), round(-ang, 1), [round(c / 255, 3) for c in col[::-1]]])
res['cars'] = cars
json.dump(res, open(OUT, 'w'), separators=(',', ':'))
for k in ('asphalt', 'paving', 'lawn', 'scrub', 'pool'):
    v = res[k]
    print(k, len(v), round(sum(p['area'] for p in v)), sum(len(p['outer']) + sum(len(h) for h in p['holes']) for p in v))
print('markings', len(marks), 'trees', len(trees), 'in parcel', sum(t[3] for t in trees), 'cars', len(cars))
pal = np.array([[255,0,255],[60,60,60],[180,180,180],[40,160,40],[120,200,230],[230,200,60],[120,60,20],[0,0,0],[255,255,255],[50,110,90]], np.uint8)
vis = pal[lab]
for t in trees:
    x = int(t[0] / K + SD.ORIGIN_PX[0] - X0); y = int(-t[1] / K + SD.ORIGIN_PX[1] - Y0)
    cv2.circle(vis, (x, y), 3, (0, 0, 255), -1)
cv2.imwrite('landcover_clean_vis.jpg', cv2.resize(vis, (W // 2, H // 2), interpolation=cv2.INTER_NEAREST))
