# Image to Desmos

A tiny Flask app that turns an image into Desmos curves. It previews the OpenCV cleanup, skeleton, and Potrace result so every setting can be tuned—or each optional stage disabled—before opening the full-screen graph.

```bash
python -m pip install -r requirements.txt
python main.py
```

Open `http://127.0.0.1:5000`, choose an image, tune the stages, and select **Open in Desmos**.
