# CAPGUI

## Note:
This GUI for Stable Cascade using ComfyUI as it's backend is experimental and not exactly foolproofed yet. Expect things to require a small amount of manual work to occur by the end user before it's fully usable.

**ComfyUI's backend is a hard requirement for local generations currently.**

## Quick Start:
* All: Install ComfyUI and it's dependancies, for Windows, use the portable install, or use your existing ComfyUI installation.

* Windows: Install Python 3.10.9 or later, Git Clone this repo then: double click `start_gui.bat`
* Linux: Install Python 3.10.9 or later, `pip install -r requirements.txt`, run `python cap_app_installer.py --gradio` then `python cap_app.py`.
* Mac: Install Python 3.10.9 or later, `pip install -r requirements.txt`, run `python cap_app_installer.py --gradio` then `python cap_app.py`.

These instructions don't work until venv support on Linux works:
* Linux: Install Python 3.10.9 or later, ~~Git Clone this repo then type in a terminal: `bash start_gui.sh`~~
* Mac: Install Python 3.10.9 or later, ~~Git Clone this repo then type in a terminal: `bash start_gui.sh`~~

An installer browser tab should automatically launch and offer to automatically install models, ControlNets etc directly into your chosen ComfyUI install. If the machine is headless and runs over the network - use it's IP address instead. It's expected that CAPGUI and ComfyUI are to be installed on the same machine, but is not required due to ComfyUI's API. If you are separating the two - ensure you update the remote instance manually.

## Updating:
If you downloaded this repository with Git, just `git pull`.

## External Dependancies:
[ComfyUI for Local Generation](https://github.com/comfyanonymous/ComfyUI/) (No knowledge of nodes required.)

If you're too worried about breaking or modifying your existing ComfyUI installation, download and install another copy of ComfyUI, preferably to another directory to avoid it - this way nothing will be accidentially overwritten.

## Optional External Dependancies:
If you have an addon for ComfyUI that adds a new sampler, or scheduler that is directly added to the basic KSampling node, feel free to write a PR adding them.

[Euler SMEA Sampling](https://github.com/Koishi-Star/Euler-Smea-Dyn-Sampler/)
Adds SMEA, DY, Euler Negative sampling support, samplers that are added by this extension are marked as (Ext) in the sampler dropdown.