import cv2, sys
src, x0, y0, x1, y1, step, scale, out = sys.argv[1], *map(int, sys.argv[2:7]), float(sys.argv[7]), sys.argv[8]
im = cv2.imread(src)[y0:y1, x0:x1].copy()
im = cv2.resize(im, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
for gx in range((x0//step+1)*step, x1, step):
    X = int((gx-x0)*scale); major = gx % (step*2) == 0
    cv2.line(im, (X,0), (X,im.shape[0]), (0,255,255) if major else (0,180,255), 1)
    cv2.putText(im, str(gx), (X+2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,0,255), 1)
for gy in range((y0//step+1)*step, y1, step):
    Y = int((gy-y0)*scale); major = gy % (step*2) == 0
    cv2.line(im, (0,Y), (im.shape[1],Y), (0,255,255) if major else (0,180,255), 1)
    cv2.putText(im, str(gy), (2, Y-3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,0,255), 1)
cv2.imwrite(out, im, [cv2.IMWRITE_JPEG_QUALITY, 92])
print(out, im.shape)
