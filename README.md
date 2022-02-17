# Simple Material Helper

This is an addon for Blender 2.80+.

It adds helpers for simplifying working with materials.

This is intended for use in the context of Zelda64 modding.

## Notes for development

Create virtual environment, activate it and install `fake-bpy-module`:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install fake-bpy-module-latest
```

Create a link to the addon file in Blender's addons folder:

```sh
ln simple_material_helper.py ~/.config/blender/3.0/scripts/addons/
```
