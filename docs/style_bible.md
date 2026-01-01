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
**Day (Town)**
- Key: warm directional `#FFE6C7`, intensity `1.0–1.3`
- Fill: cool ambient `#BBD4FF`, intensity `0.2–0.4`
- Soft shadows on

**Night (Town)**
- Key: cool directional `#7FA7FF`, intensity `0.4–0.7`
- Ambient: `0.1–0.2`
- Practical lights: lamps/windows emissive

**Mafia Lair**
- Key: red `#FF4D4D`, intensity `0.8–1.2`
- Ambient: `0.1`
- Light fog/haze if available

**Detective Office**
- Key: blue `#4DA3FF`, intensity `0.8–1.1`
- Accent: warm desk lamp `#FFC857`

## Town Square Blockout (Scene A)
Top-down plan, centered at (0,0):
- Round table at center (0,0)
- 4–6 buildings around a ring (radius ~9–11m)
- 4 street lamps at cardinal points (~6m radius)
- Sidewalk ring around the square (~3m radius)
- Small trees/props between buildings
- Characters stand in a semi-circle arc behind the table (no chairs, no sitting)

## Character Rules
- Big head, chunky limbs, minimal facial detail
- Keep silhouettes bold and readable
- No photo textures or micro-detail
- All characters use the same plastic material

## fal.ai Prompt Pack (Characters via Hunyuan3D)
Use reference images for brainrot memes + these style modifiers. A-pose recommended.

**Base humanoid** (text-only)
```
stylized plastic toy humanoid, blocky proportions, big head, chunky limbs,
minimal facial features, solid colors, clean silhouette, no textures
```

**Bombardiro Crocodilo** (use reference image +)
```
stylized plastic, blocky proportions, toy-like, clean silhouette, solid colors, no textures
```

**Tralalero Tralala** (use reference image +)
```
stylized plastic, blocky proportions, toy-like, clean silhouette, solid colors, no textures
```

## fal.ai Prompt Pack (Props via Trellis 2 or Hunyuan3D)
**House (modular)**
```
low-poly house, clean boxy shape, simple windows, no textures,
separate roof and body, solid colors
```

**Street lamp**
```
low-poly street lamp, clean silhouette, simple geometry, no textures,
separate lamp head and pole
```

**Round table**
```
low-poly round table, simple legs, clean silhouette, no textures,
separate tabletop and base
```

## Consistency Checklist (Required)
- Override all materials to palette in-engine
- Normalize scale (humanoids ~1.7m)
- Pivot at feet (characters) and base (props)
- Re-center models to origin
