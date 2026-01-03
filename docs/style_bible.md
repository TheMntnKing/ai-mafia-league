# Style Bible (Phase 10)

Roblox-adjacent, stylized plastic look for the replay viewer.
Goal: meme-friendly, kid/teen pleasing, but cinematic and slightly serious via lighting.

## Scale
- World scale: 1 unit = 1 meter
- Humanoid height: ~1.7m
- Table height: ~0.75m, diameter ~2.2m
- Lamp height: ~3.0m

## Palette (hex)
**Neutrals**
- Bone: `#F5F3EF`
- Light Gray: `#D9DDE3`
- Mid Gray: `#9AA3AF`
- Charcoal: `#3D4350`

**Accents**
- Blue: `#2F7AE5`
- Red: `#E54B4B`
- Yellow: `#F2C94C`
- Green: `#2ECC71`
- Orange: `#F2994A`
- Purple: `#8E44AD`

**Sky / Fog**
- Day Sky: `#BFD7FF`
- Night Sky: `#0E1B3A`

## Materials (R3F defaults)
**Plastic (default)**
- metalness: `0.0`
- roughness: `0.45–0.60`
- clearcoat: `0.05`
- specular: `0.3`
- base color from palette

**Glass (optional for windows)**
- metalness: `0.0`
- roughness: `0.05–0.15`
- transmission: `0.7–0.9`
- tint: `#BFD7FF`

**Emissive (lamps/windows)**
- emissive color: `#FFC857`
- emissive intensity: `0.6–1.2`

## Lighting Rules

All scenes use a **3-point setup**: ambient + key directional + fill directional. No shadows (cleaner stylized look).

**Day (Town)**
- Ambient: cool `#BBD4FF`, intensity `0.4`
- Key: warm directional `#FFE6C7`, intensity `1.2`
- Fill: neutral directional `#ffffff`, intensity `0.5`

**Night (Town)**
- Ambient: cool `#7FA7FF`, intensity `0.2`
- Key: cool directional `#7FA7FF`, intensity `0.6`
- Fill: neutral directional `#ffffff`, intensity `0.3`

**Mafia Lair**
- Ambient: dark red `#3B1A1A`, intensity `0.15`
- Key: red directional `#FF4D4D`, intensity `1.0`
- Fill: neutral directional `#ffffff`, intensity `0.4` (preserves character colors)

**Detective Office**
- Ambient: neutral `#D9DDE3`, intensity `0.35`
- Key: warm directional `#FFE6C7`, intensity `0.9`
- Fill: neutral directional `#ffffff`, intensity `0.6`

## Scene Pipeline

See `docs/scene_pipeline.md` for asset sources, Blender assembly, and export rules.

## Town Square Blockout (Scene A)
Top-down plan, centered at (0,0):
- Round table at center (0,0)
- 4–6 buildings around a ring (radius ~9–11m)
- 4 street lamps at cardinal points (~6m radius)
- Sidewalk ring around the square (~3m radius)
- Small trees/props between buildings
- Characters stand in a semi-circle arc behind the table (no chairs, no sitting)

## Character Styling

See `docs/character_pipeline.md` for character identity, pose, and stylization rules.

## Consistency Checklist (Required)
- Keep generated textures (Textured Mesh = Enabled in Hunyuan3D preserves colors)
- Override material properties in code: metalness=0, roughness=0.5, clearcoat=0.05 (fixes Hunyuan3D's metallic defaults)
- Normalize scale (humanoids ~1.7m)
- Pivot at feet (characters) and base (props)
- Re-center models to origin
