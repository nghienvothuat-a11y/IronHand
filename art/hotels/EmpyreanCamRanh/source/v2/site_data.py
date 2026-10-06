"""Measured site data for the Empyrean Cam Ranh v2 rebuild.

All plan coordinates were traced on web-mercator aerial imagery of the resort
(12.0266 N, 109.2169 E): Esri World Imagery zoom 18 (near-nadir, used for
footprints) resampled onto the Bing Aerial zoom 19 tile grid (used for detail).
Pixel coordinates are on that zoom-19 mosaic whose top-left tile is
(x=421196, y=244495). One pixel is 0.29203 m on the ground.

World frame: metres, origin at the centre of Arena Square, +X east, +Y true north.

Heights and floor counts come from the Vietnam Record certificate (22 Sep 2023)
and on-site photographs; see RESEARCH notes referenced in README_V2.txt.
"""
import math

M_PER_PX = 0.29203
ORIGIN_PX = (1590.0, 1520.0)   # Arena Square centre on the z19 mosaic


def px(x, y):
    """Mosaic pixel -> world metres (X east, Y north)."""
    return ((x - ORIGIN_PX[0]) * M_PER_PX, -(y - ORIGIN_PX[1]) * M_PER_PX)


def pts(seq):
    return [px(x, y) for x, y in seq]


# Villa grid frame: the resort parcel is rotated 22.9 deg (image space) from the
# mosaic axes.  Coordinates (xr, yr) were read on a rotated crop whose pixel
# (0,0) is u=-760, v=-420 in a frame pivoting on ORIGIN_PX.
PARCEL_ROT_DEG = 22.9


def rot(xr, yr):
    u, v = xr - 760.0, yr - 420.0
    a = math.radians(PARCEL_ROT_DEG)
    c, s = math.cos(a), math.sin(a)
    x = c * u + s * v + ORIGIN_PX[0]
    y = -s * u + c * v + ORIGIN_PX[1]
    return px(x, y)


# Parcel axis (unit vector of the villa rows, world space) and its normal.
_a = math.radians(PARCEL_ROT_DEG)
PARCEL_U = (math.cos(_a), math.sin(_a))      # image y down -> world y up flips sign
PARCEL_V = (math.sin(_a), -math.cos(_a))

# ---------------------------------------------------------------------------
# Towers.  outer = convex side (away from the pool court), inner = concave side.
# Both run from the north-east wing tip, around the rounded head, to the east
# wing tip.  plateau_* are points near where the full-height roof ends.
# ---------------------------------------------------------------------------
TOWERS = [
    dict(
        id="Light", code="A1", position="north inland",
        floors=18, tip_floors=4, ground_h=6.0, floor_h=3.55, roof_level_h=4.6,
        accent="terracotta", rooms=1174,
        outer=[(1045, 850), (985, 880), (950, 903), (915, 925), (890, 950), (860, 975),
               (835, 1000), (818, 1025), (800, 1050), (785, 1075), (765, 1100), (750, 1135),
               (735, 1170), (724, 1205), (722, 1240), (728, 1270), (740, 1293), (757, 1312),
               (778, 1328), (803, 1342), (830, 1353), (860, 1361), (900, 1366), (950, 1369),
               (1050, 1371), (1150, 1370), (1268, 1366)],
        inner=[(1105, 893), (1040, 935), (985, 982), (935, 1035), (895, 1080), (868, 1125),
               (848, 1152), (825, 1175), (808, 1205), (800, 1240), (806, 1268), (826, 1287),
               (858, 1297), (900, 1299), (1000, 1300), (1100, 1301), (1200, 1301), (1268, 1299)],
        plateau=[(840, 1080), (985, 1335)],
        podium_px=[(880, 1175), (884, 1222), (874, 1262)],
        entrance_px=(724, 1225),
        head_px=[(765, 1100), (900, 1366)],
    ),
    dict(
        id="Sea", code="A2", position="north beachfront",
        floors=20, tip_floors=4, ground_h=6.0, floor_h=3.55, roof_level_h=4.6,
        accent="blue", rooms=1182,
        outer=[(1975, 600), (1920, 640), (1870, 675), (1830, 705), (1790, 735), (1755, 765),
               (1720, 795), (1695, 825), (1675, 850), (1655, 880), (1640, 910), (1631, 950),
               (1631, 990), (1640, 1020), (1660, 1050), (1690, 1075), (1730, 1095), (1780, 1105),
               (1830, 1110), (1900, 1112), (2000, 1112), (2100, 1110), (2195, 1105)],
        inner=[(2012, 650), (1955, 690), (1905, 728), (1862, 772), (1828, 815), (1795, 857),
               (1762, 893), (1730, 922), (1710, 955), (1704, 985), (1712, 1012), (1735, 1033),
               (1770, 1045), (1830, 1048), (1900, 1049), (2000, 1049), (2100, 1048), (2195, 1046)],
        plateau=[(1720, 850), (1880, 1080)],
        podium_px=[(1760, 930), (1792, 975), (1810, 1022)],
        entrance_px=(1632, 975),
        head_px=[(1675, 850), (1780, 1105)],
    ),
    dict(
        id="Sand", code="B2", position="south beachfront",
        floors=8, tip_floors=4, ground_h=5.0, floor_h=3.3, roof_level_h=4.0,
        accent="grey", rooms=576,
        outer=[(2290, 1425), (2250, 1450), (2210, 1475), (2175, 1500), (2150, 1525), (2120, 1555),
               (2095, 1580), (2075, 1605), (2050, 1630), (2030, 1660), (2010, 1690), (1993, 1720),
               (1980, 1755), (1975, 1790), (1978, 1825), (1990, 1855), (2010, 1880), (2035, 1902),
               (2065, 1920), (2100, 1932), (2150, 1938), (2250, 1942), (2350, 1943), (2450, 1942),
               (2528, 1938)],
        inner=[(2355, 1478), (2300, 1512), (2250, 1545), (2210, 1578), (2175, 1612), (2145, 1650),
               (2118, 1688), (2088, 1716), (2065, 1740), (2053, 1772), (2053, 1805), (2066, 1835),
               (2092, 1857), (2128, 1868), (2180, 1872), (2300, 1873), (2400, 1872), (2528, 1870)],
        plateau=[(2245, 1475), (2345, 1905)],
        podium_px=[(2118, 1745), (2134, 1792), (2132, 1832)],
        entrance_px=(1976, 1790),
        head_px=[(2030, 1660), (2100, 1932)],
    ),
    dict(
        id="Wind", code="B1", position="south inland",
        floors=8, tip_floors=4, ground_h=5.0, floor_h=3.3, roof_level_h=4.0,
        accent="grey", rooms=601,
        outer=[(1450, 1865), (1405, 1900), (1370, 1925), (1340, 1950), (1310, 1972), (1280, 1997),
               (1255, 2020), (1230, 2045), (1210, 2070), (1190, 2097), (1172, 2125), (1158, 2160),
               (1150, 2195), (1150, 2230), (1157, 2262), (1172, 2293), (1195, 2320), (1225, 2343),
               (1262, 2360), (1305, 2372), (1350, 2379), (1450, 2383), (1550, 2384), (1695, 2382)],
        inner=[(1515, 1915), (1465, 1955), (1420, 1990), (1380, 2022), (1345, 2058), (1315, 2095),
               (1290, 2130), (1265, 2160), (1243, 2192), (1230, 2228), (1235, 2262), (1255, 2288),
               (1290, 2308), (1340, 2317), (1450, 2318), (1550, 2318), (1695, 2318)],
        plateau=[(1395, 1935), (1545, 2350)],
        podium_px=[(1300, 2150), (1310, 2230), (1300, 2285)],
        entrance_px=(1151, 2212),
        head_px=[(1210, 2070), (1305, 2372)],
    ),
]

# ---------------------------------------------------------------------------
# Shopvillas (126 units in pairs, 3 storeys, lot 8.8 m x 17.6 m).  Each entry is
# a twin block (two units) as a rectangle in the rotated crop frame
# (xr0, yr0, xr1, yr1) -> rotated pixel units, axis-aligned to the parcel grid.
# ---------------------------------------------------------------------------
VILLA_BLOCKS_ROT = [
    # west cluster, north-west strip
    (18, 125, 75, 170), (80, 125, 138, 170),
    (18, 205, 75, 252), (80, 205, 138, 252),
    (18, 262, 75, 310), (80, 262, 138, 310),
    # under the ballroom
    (152, 270, 207, 348), (210, 270, 270, 348), (288, 270, 342, 348), (348, 270, 405, 348),
    # east of the ballroom
    (432, 165, 488, 222), (493, 165, 548, 222),
    (433, 245, 485, 300), (490, 245, 542, 300),
    (430, 307, 482, 355), (488, 307, 545, 355),
    # west cluster, south half
    (8, 470, 62, 520), (65, 470, 130, 520), (145, 470, 200, 520), (205, 470, 262, 520),
    (285, 470, 340, 520), (345, 470, 400, 520), (420, 470, 475, 520), (480, 470, 540, 520),
    (8, 525, 62, 560), (65, 525, 130, 560), (145, 525, 200, 560), (205, 525, 262, 560),
    (285, 525, 340, 560), (345, 525, 400, 560), (420, 525, 475, 560), (480, 525, 540, 560),
    (8, 580, 60, 630), (62, 580, 128, 630), (140, 580, 195, 630), (200, 580, 258, 630),
    (278, 580, 335, 630), (338, 580, 395, 630), (420, 580, 472, 630), (478, 580, 532, 630),
    (5, 635, 60, 690), (62, 635, 130, 690), (140, 635, 195, 690), (200, 635, 258, 690),
    (282, 635, 332, 690), (336, 635, 392, 690), (415, 635, 468, 690), (474, 635, 532, 690),
    # east cluster
    (1032, 165, 1110, 222), (1118, 165, 1175, 222),
    (1055, 265, 1108, 318), (1113, 265, 1178, 318), (1208, 265, 1262, 318), (1268, 265, 1332, 318),
    (1055, 322, 1108, 370), (1113, 322, 1178, 370), (1208, 322, 1262, 370), (1268, 322, 1332, 370),
    (1048, 485, 1102, 535), (1108, 485, 1162, 535), (1203, 485, 1255, 535), (1262, 485, 1315, 535),
    (1048, 540, 1102, 595), (1108, 540, 1162, 595), (1205, 540, 1258, 595), (1263, 540, 1315, 595),
    (1013, 640, 1095, 690), (1103, 640, 1162, 690),
]

# Ballroom / event hall with dark gridded roof (rotated frame), height ~9 m.
BALLROOM_ROT = (145, 115, 410, 245)
# Two-storey white service block by the north-west parking.
SERVICE_BLOCKS_ROT = [(118, 60, 160, 118)]

# ---------------------------------------------------------------------------
# Arena Square (world metres from origin).  Radial checker plaza with a stepped
# grandstand on the west half, a water-music stage on the east, statue centre.
# ---------------------------------------------------------------------------
ARENA = dict(
    centre_px=(1590, 1520),
    plaza_radius_m=48.0,
    grandstand_outer_m=56.0,
    ring_path_inner_m=60.0,
    ring_path_outer_m=66.0,
    stage_px=(1705, 1520),
    statue_px=(1600, 1515),
    checker_focus_px=(1650, 1500),
)

# West lagoon by the main road: long lens of dark water with a triangular
# viewing deck pushing in from the east side.
WEST_LAKE_PX = [(700, 1615), (735, 1650), (765, 1720), (792, 1790), (808, 1826), (790, 1832),
                (822, 1852), (838, 1890), (852, 1945), (868, 2000), (878, 2050), (872, 2080),
                (858, 2090), (835, 2052), (800, 1990), (770, 1930), (745, 1870), (720, 1800),
                (705, 1730), (697, 1670)]

# Low fan-shaped pavilion south-east of Sand tower (ribbed roof).
SAND_PAVILION_PX = dict(
    outer=[(2532, 1834), (2575, 1832), (2625, 1838), (2675, 1850), (2720, 1870), (2760, 1900),
           (2790, 1935), (2812, 1978)],
    inner=[(2545, 1912), (2600, 1918), (2650, 1928), (2700, 1952), (2735, 1980), (2758, 2010)],
)

# Small utility buildings (rotated frame boxes) seen in aerial photos.
UTILITY_BOXES_PX = [
    ((2075, 2040), (2120, 2075)),
]

# Sand-court water park (traced rim, light lagoon water, dark rectangular basin).
LAGOON_RIM_PX = [(2470, 1405), (2490, 1420), (2500, 1445), (2510, 1470), (2540, 1478), (2560, 1490), (2565, 1510),
                 (2550, 1530), (2565, 1550), (2590, 1552), (2605, 1570), (2600, 1600), (2585, 1615), (2565, 1625),
                 (2560, 1645), (2580, 1660), (2610, 1660), (2640, 1662), (2665, 1680), (2690, 1710), (2700, 1740),
                 (2730, 1780), (2745, 1795), (2730, 1805), (2700, 1790), (2665, 1765), (2630, 1752), (2600, 1758),
                 (2560, 1765), (2530, 1770), (2500, 1775), (2460, 1778), (2420, 1772), (2390, 1765), (2365, 1745),
                 (2350, 1720), (2355, 1690), (2340, 1665), (2330, 1640), (2335, 1610), (2350, 1590), (2370, 1570),
                 (2365, 1545), (2370, 1525), (2390, 1510), (2420, 1500), (2445, 1495), (2460, 1470), (2462, 1440)]
LAGOON_BASIN_PX = [(2433, 1535), (2525, 1517), (2555, 1690), (2462, 1708)]
# Wind-court pool: capsule (end A, end B, radius px) and a round plunge pool (centre, radius px).
WIND_POOL_PX = ((1655, 2095), (1740, 2052), 19)
WIND_SMALL_POOL_PX = ((1607, 2112), 17)

# White tensile shade canopies in the tower gardens (centre px, approx size m).
CANOPIES_PX = [((1190, 1148), 11.0), ((1575, 2025), 12.0)]

# Shopvilla districts (rotated crop frame): paved lanes with tree planters.
VILLA_DISTRICTS_ROT = [(0, 105, 150, 360), (150, 250, 560, 365), (420, 150, 560, 365), (0, 455, 560, 705),
                       (1020, 150, 1345, 380), (1030, 470, 1340, 700),
                       (0, 355, 535, 470), (985, 375, 1345, 475)]   # central promenades toward Arena Square
