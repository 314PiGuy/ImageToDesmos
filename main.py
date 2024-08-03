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


def trace(file):
    bmp = potrace.Bitmap(detect(file))
    path = bmp.trace(2, potrace.POTRACE_TURNPOLICY_MINORITY, 1.0, 1, .5)

    beziers = []

    for curve in path:
        #go through all the segments in all the curves and desmosify them
        start = curve.start_point
        segments = curve.segments
        for segment in segments:
            #this thing doesnt work for some reason its non unpackable even though according to the docs is shouldnt be
            x0, y0 = start, start
            if segment.is_corner:
                x1, y1 = segment.c
                x2, y2 = segment.end_point
                s1, s2 = makeCorner(x0, x1, x2, y0, y1, y2)
                beziers.append(s1)
                beziers.append(s2)
            else:
                x1, y1 = segment.c1
                x2, y2 = segment.c2
                x3, y3 = segment.end_point
                #need to figure out how to make a desmos format fourth order bezier curve which will probably be long and painful
                beziers.append(s)
            start = segment.end_point
            
    return beziers
    
b = trace('rick.jpg')