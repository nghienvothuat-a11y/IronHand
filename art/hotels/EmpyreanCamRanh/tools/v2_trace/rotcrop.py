# rotate mosaic about pivot so parcel axes align; grid in rotated frame (u,v) px
import cv2, sys, math, numpy as np
src, ang, px, py, u0, v0, u1, v1, step, scale, out = sys.argv[1], float(sys.argv[2]), *map(float, sys.argv[3:5]), *map(int, sys.argv[5:9]), int(sys.argv[9]), float(sys.argv[10]), sys.argv[11]
im = cv2.imread(src)
# rotated frame: u = cos*(x-px) - sin*(y-py) ; v = sin*(x-px) + cos*(y-py), with rotation angle ang (deg, ccw in image => counter the road slope)
a = math.radians(ang)
W, H = u1-u0, v1-v0
# map from output pixel (i,j) -> u = u0 + i/scale, v = v0 + j/scale -> x,y
M = np.zeros((2,3))
c, s = math.cos(a), math.sin(a)
# inverse: x = c*u + s*v + px ; y = -s*u + c*v + py
M[0] = [c/scale, s/scale, c*u0 + s*v0 + px]
M[1] = [-s/scale, c/scale, -s*u0 + c*v0 + py]
outim = cv2.warpAffine(im, M, (int(W*scale), int(H*scale)), flags=cv2.WARP_INVERSE_MAP | cv2.INTER_CUBIC)
for gu in range((u0//step+1)*step, u1, step):
    X = int((gu-u0)*scale); cv2.line(outim,(X,0),(X,outim.shape[0]),(0,255,255),1)
    cv2.putText(outim,str(gu),(X+2,12),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),1)
for gv in range((v0//step+1)*step, v1, step):
    Y = int((gv-v0)*scale); cv2.line(outim,(0,Y),(outim.shape[1],Y),(0,255,255),1)
    cv2.putText(outim,str(gv),(2,Y-2),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),1)
cv2.imwrite(out, outim)
print(out, outim.shape)
