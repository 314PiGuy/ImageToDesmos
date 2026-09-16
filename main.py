import base64

import cv2
import numpy as np
import potrace
from flask import Flask, jsonify, render_template, request
from skimage.morphology import skeletonize

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024


def value(name, default, low, high, cast=float):
    try:
        return max(low, min(high, cast(request.form.get(name, default))))
    except (TypeError, ValueError):
        return default


def enabled(name, default=True):
    return request.form.get(name, str(default).lower()) == "true"


def parameters():
    policies = {
        name: getattr(potrace, "TURNPOLICY_" + name.upper())
        for name in ("black", "white", "left", "right", "minority", "majority", "random")
    }
    policy = request.form.get("turnpolicy", "minority")
    return {
        "resize_enabled": enabled("resize_enabled"),
        "size": value("size", 900, 1, 4000, int),
        "mode": request.form.get("mode", "threshold"),
        "blur_enabled": enabled("blur_enabled"),
        "blur": value("blur", 3, 1, 51, int),
        "threshold": value("threshold", 145, 0, 255, int),
        "canny_low": value("canny_low", 35, 0, 255, int),
        "canny_high": value("canny_high", 130, 0, 255, int),
        "join_enabled": enabled("join_enabled"),
        "join": value("join", 1, 0, 32, int),
        "close_enabled": enabled("close_enabled"),
        "close": value("close", 1, 0, 32, int),
        "skeleton_enabled": enabled("skeleton_enabled"),
        "skeleton_kernel": value("skeleton_kernel", 3, 3, 15, int),
        "prune_enabled": enabled("prune_enabled"),
        "prune": value("prune", 4, 0, 2000, int),
        "trace_enabled": enabled("trace_enabled"),
        "turdsize": value("turdsize", 2, 0, 2000, int),
        "turnpolicy": policies.get(policy, policies["minority"]),
        "alphamax": value("alphamax", 1.0, 0, 2),
        "opticurve": enabled("opticurve"),
        "opttolerance": value("opttolerance", 0.2, 0, 10),
    }


def remove_flecks(image, minimum):
    if not minimum:
        return image
    count, labels, stats, _ = cv2.connectedComponentsWithStats(image, connectivity=8)
    clean = np.zeros_like(image)
    for label in range(1, count):
        if stats[label, cv2.CC_STAT_AREA] >= minimum:
            clean[labels == label] = 255
    return clean


def process(image, params):
    height, width = image.shape[:2]
    scale = min(1, params["size"] / max(height, width))
    if params["resize_enabled"] and scale < 1:
        size = (max(1, round(width * scale)), max(1, round(height * scale)))
        image = cv2.resize(image, size, interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = gray
    if params["blur_enabled"]:
        blurred = cv2.GaussianBlur(gray, (params["blur"], params["blur"]), 0)
    if params["mode"] == "canny":
        binary = cv2.Canny(blurred, params["canny_low"], params["canny_high"])
        if params["join_enabled"] and params["join"]:
            radius = params["join"]
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1,) * 2)
            binary = cv2.dilate(binary, kernel)
    else:
        _, binary = cv2.threshold(blurred, params["threshold"], 255, cv2.THRESH_BINARY_INV)

    if params["close_enabled"] and params["close"]:
        radius = params["close"]
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1,) * 2)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)


    skeleton = (
        skeletonize(binary).astype(np.uint8) * 255
        if params["skeleton_enabled"] else binary
    )
    if params["prune_enabled"]:
        skeleton = remove_flecks(skeleton, params["prune"])
    return binary, skeleton


def number(value):
    return f"{value:.2f}".rstrip("0").rstrip(".")


def point(value, height, flip=False):
    x, y = value if isinstance(value, tuple) else (value.x, value.y)
    return number(x), number(height - y if flip else y)


def line(a, b):
    return rf"\left((1-t)({a[0]})+t({b[0]}),(1-t)({a[1]})+t({b[1]})\right)"


def bezier(points):
    terms = ("(1-t)^3", "3(1-t)^2t", "3(1-t)t^2", "t^3")
    x = "+".join(f"{term}({p[0]})" for term, p in zip(terms, points))
    y = "+".join(f"{term}({p[1]})" for term, p in zip(terms, points))
    return rf"\left({x},{y}\right)"


def trace(skeleton, params):
    height, width = skeleton.shape
    bitmap = potrace.Bitmap(skeleton > 0)
    path = bitmap.trace(
        params["turdsize"], params["turnpolicy"], params["alphamax"],
        params["opticurve"], params["opttolerance"]
    )
    expressions, svg_parts = [], []
    for curve in path:
        start = curve.start_point
        svg = ["M", *point(start, height)]
        for segment in curve.segments:
            graph_start = point(start, height, True)
            if segment.is_corner:
                corner = point(segment.c, height, True)
                end = point(segment.end_point, height, True)
                expressions.extend((line(graph_start, corner), line(corner, end)))
                svg += ["L", *point(segment.c, height), "L", *point(segment.end_point, height)]
            else:
                graph_points = [
                    graph_start, point(segment.c1, height, True),
                    point(segment.c2, height, True), point(segment.end_point, height, True)
                ]
                expressions.append(bezier(graph_points))
                svg += [
                    "C", *point(segment.c1, height), *point(segment.c2, height),
                    *point(segment.end_point, height)
                ]
            start = segment.end_point
        svg.append("Z")
        svg_parts.append(" ".join(svg))

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">'
        '<rect width="100%" height="100%" fill="white"/>'
        f'<path d="{" ".join(svg_parts)}" fill="#111827" fill-rule="evenodd"/></svg>'
    )
    return expressions, "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def png(image):
    ok, data = cv2.imencode(".png", image)
    if not ok:
        raise ValueError("Could not render preview")
    return "data:image/png;base64," + base64.b64encode(data).decode()


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/preview")
def preview():
    upload = request.files.get("image")
    if not upload:
        return jsonify(error="Choose an image first."), 400
    image = cv2.imdecode(np.frombuffer(upload.read(), np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        return jsonify(error="That file is not a readable image."), 400

    params = parameters()
    processed, skeleton = process(image, params)
    if params["trace_enabled"]:
        expressions, traced = trace(skeleton, params)
    else:
        expressions, traced = [], png(skeleton)
    height, width = skeleton.shape
    return jsonify(
        processed=png(processed), skeleton=png(skeleton), traced=traced,
        expressions=expressions, width=width, height=height, segments=len(expressions),
        trace_enabled=params["trace_enabled"]
    )


@app.get("/desmos")
def desmos():
    return render_template("desmos.html")


if __name__ == "__main__":
    app.run(debug=True)
