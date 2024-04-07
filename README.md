# CAPGUI

## Note:
This GUI for Stable Cascade using ComfyUI is experimental and not exactly foolproofed yet. Expect things to require a small amount of manual work to occur by the end user before it's fully usable.

## Quick and Dirty Installation Features:
`pip install gradio websocket-client pillow requests`

## Quick Start:
`python3 cap_app.py`
`python cap_app.py`

Navigate to the Settings tab, locate your local instance of ComfyUI and copy the file path to it's root directory. CAP GUI will install a special CAPGUI custom node folder into it, as well as download Stable Cascade models directly into your ComfyUI with it's own subfolders to avoid file collisions.

If you're too worried about breaking your existing ComfyUI installation, download and install another copy of ComfyUI, preferably to another directory to avoid it - this way nothing will be accidentially overwritten.