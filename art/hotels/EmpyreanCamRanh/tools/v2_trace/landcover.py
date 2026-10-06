"""Classify the near-nadir mosaic into landcover classes -> WORKDIR/landcover_raw.png.

  python landcover.py WORKDIR      (requires numpy and opencv-python)
"""
import cv2, numpy as np
import sys, os
os.chdir(sys.argv[1])
E = cv2.imread('esri_on_bing_grid.jpg')
img = E
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.int32)
H, S, V = hsv[...,0], hsv[...,1], hsv[...,2]
b, g, r = [img[...,i].astype(np.int32) for i in range(3)]
cls = np.zeros(H.shape, np.uint8)  # 0 unknown
# classes: 1 asphalt, 2 paving(light grey), 3 grass/veg, 4 sand, 5 water(pool cyan), 6 deep water/sea, 7 shadow, 8 white roof/bright
water = (H >= 80) & (H <= 110) & (S > 70) & (V > 90)
sea = (H >= 80) & (H <= 115) & (S > 60) & (V <= 90)
veg = (H >= 30) & (H <= 80) & (S > 45) & (V > 35)
sand = (H >= 8) & (H <= 28) & (S > 30) & (S < 120) & (V > 150)
asph = (S < 45) & (V >= 55) & (V < 125)
pav = (S < 40) & (V >= 125) & (V < 215)
bright = (S < 40) & (V >= 215)
shadow = (V < 55)
for k, m in [(3, veg), (4, sand), (1, asph), (2, pav), (8, bright), (5, water), (6, sea), (7, shadow)]:
    cls[m & (cls == 0)] = k
pal = np.array([[255,0,255],[60,60,60],[180,180,180],[40,160,40],[120,200,230],[230,200,60],[120,60,20],[0,0,0],[255,255,255]], np.uint8)
vis = pal[cls]
cv2.imwrite('landcover_raw.png', cls)
cv2.imwrite('landcover_vis.jpg', cv2.resize(vis, (1792, 1664), interpolation=cv2.INTER_NEAREST))
print(np.bincount(cls.ravel(), minlength=9) / cls.size)
