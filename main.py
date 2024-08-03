import cv2
import potrace


def detect(file):
    #make it black and white and then trace it so potrace can get the lines
    image = cv2.imread(file)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    return edges

def makeCorner(x0, x1, x2, y0, y1, y2):
    #desmos format the corner as 2 straight lines
    expr1 = rf'\left(\left(1-t\right){x0}+t{x1},\left(1-t\right){y0}+t{y1}\right)'
    expr2 = rf'\left(\left(1-t\right){x1}+t{x2},\left(1-t\right){y1}+t{y2}\right)'
    return expr1, expr2

def makeCurve(x0, x1, x2, x3, y0, y1, y2, y3):
    #fourth order bezier in desmos format
    expr = rf'\left(\left(1-t\right)\left(\left(1-t\right)\left(\left(1-t\right){x0}+t{x1}\right)+t\left(\left(1-t\right){x1}+t{x2}\right)\right)+t\left(\left(1-t\right)\left(\left(1-t\right){x1}+t{x2}\right)+t\left(\left(1-t\right){x2}+t{x3}\right)\right),\left(1-t\right)\left(\left(1-t\right)\left(\left(1-t\right){y0}+t{y1}\right)+t\left(\left(1-t\right){y1}+t{y2}\right)\right)+t\left(\left(1-t\right)\left(\left(1-t\right){y1}+t{y2}\right)+t\left(\left(1-t\right){y2}+t{y3}\right)\right)\right)'
    return expr

def trace(file):
    bmp = potrace.Bitmap(detect(file))
    path = bmp.trace(2, potrace.POTRACE_TURNPOLICY_MINORITY, 1.0, 1, .5)

    beziers = []

    for curve in path:
        #go through all the segments in all the curves and desmosify them
        start = curve.start_point
        segments = curve.segments
        for segment in segments:
            x0, y0 = start.x, start.y
            if segment.is_corner:
                x1, y1 = segment.c.x, segment.c.y
                x2, y2 = segment.end_point.x, segment.end_point.y
                s1, s2 = makeCorner(x0, x1, x2, y0, y1, y2)
                beziers.append(s1)
                beziers.append(s2)
            else:
                x1, y1 = segment.c1.x, segment.c1.y
                x2, y2 = segment.c2.x, segment.c2.y
                x3, y3 = segment.end_point.x, segment.end_point.y
                s = makeCurve(x0, x1, x2, x3, y0, y1, y2, y3)
                beziers.append(s)
            start = segment.end_point
            
    return beziers
    
b = trace('rick.jpg')

with open('output.txt', 'w') as f:
    for i in b:
        f.write(i + '\n')