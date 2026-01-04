# Viewer Art Pipeline

Single source of truth for style, character generation, and scene assembly.

## Style Targets

- Stylized mesh humanoids with blocky proportions (Roblox-adjacent silhouette, not voxel).
- 2-3 iconic features per persona (head shape, accessory, color scheme).
- Matte hard plastic surfaces, solid colors, clean silhouettes.

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
- Teal: `#32B8B0`

**Sky / Fog**
- Day Sky: `#BFD7FF`
- Night Sky: `#0E1B3A`

## Materials (R3F defaults)

**Plastic (default)**
- metalness: `0.0`
- roughness: `0.45-0.60`
- clearcoat: `0.05`
- specular: `0.3`
- base color from palette

**Glass (optional for windows)**
- metalness: `0.0`
- roughness: `0.05-0.15`
- transmission: `0.7-0.9`
- tint: `#BFD7FF`

**Emissive (lamps/windows)**
- emissive color: `#FFC857`
- emissive intensity: `0.6-1.2`

## Lighting Presets

All scenes use a 3-point setup: ambient + key directional + fill directional. No shadows.

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
- Fill: neutral directional `#ffffff`, intensity `0.4`

**Detective Office**
- Ambient: neutral `#D9DDE3`, intensity `0.35`
- Key: warm directional `#FFE6C7`, intensity `0.9`
- Fill: neutral directional `#ffffff`, intensity `0.6`

**Doctor Scene**
- Ambient: cool `#CFEDE7`, intensity `0.35`
- Key: teal directional `#32B8B0`, intensity `0.9`
- Fill: neutral directional `#ffffff`, intensity `0.6`

## Character Pipeline

**Target**: stylized mesh humanoid toy with blocky proportions
- Surface: matte hard plastic, solid colors
- Geometry: blocky, low-poly with sharp corners
- Proportions: big head (about 1/3 height), boxy body, distinct limbs
- Silhouette: clean, readable at thumbnail size
- Materials: no gradients, no photo-textures, no micro-detail, no round bevels

**API:** fal.ai (Hunyuan3D v2)
**Input:** clean 2D reference image (front or 3/4 view, clear silhouette)
**Output:** `.glb` for R3F

### Prompt (full)
```
[Task]: Transform this character into a 3D plastic toy reference sheet for game asset creation.

[Character Identity]: Preserve the character's iconic features, color scheme, and personality. Keep recognizable elements (head shape, accessories, expressions) intact.

[Pose Override]: Convert to a neutral frontal A-pose:
  - Standing upright, symmetrical stance
  - Feet shoulder-width apart
  - Arms straight and rigid at sides, angled ~30° from body
  - Palms facing inward
  - Adapt pose naturally if original anatomy requires it

[Stylization Rules]:
  - Proportions: Big head (about 1/3 height), boxy body, distinct limbs
  - Geometry: Blocky, low-poly shapes with sharp corners (Roblox-adjacent)
  - Surface: Matte hard plastic, solid colors per body part
  - NO realistic skin texture, NO gradients, NO fine detail, NO round bevels
  - Clean silhouette, simple geometric forms

[Technical Output]:
  - Background: Pure solid white (#FFFFFF)
  - Lighting: Flat, even studio lighting with minimal shadows
  - View: Front-facing, centered, symmetrical
  - Quality: Clean edges, no compression artifacts

[Goal]: Production-ready reference for 3D model generation via Hunyuan3D.
```

### Hunyuan3D v2 settings (fal.ai)

| Setting | Value | Notes |
|---------|-------|-------|
| Image Input | Clean 2D reference | Required |
| Num Inference Steps | 50 | Higher = more detail |
| Guidance Scale | 7.5 | Use 9-10 if fidelity is low |
| Octree Resolution | 256 | 512 for more detail, 128 for blockier |
| Textured Mesh | Enabled | Keep enabled - preserves colors |

Workflow:
1) Run with defaults.
2) If too smooth, increase Octree Resolution.
3) If off-model, increase Guidance Scale.
4) If too detailed, reduce Octree Resolution.

### Post-process in viewer
- Normalize pivot to floor using bounding box min.y.
- Normalize scale to ~1.7 units tall.
- Keep generated textures (colors), override material properties only if too shiny.

Example snippet (TestModel/Character loader):
```js
const box = new Box3().setFromObject(scene)
const height = box.max.y - box.min.y
const lift = -box.min.y
const scaleFactor = TARGET_HEIGHT / height

<primitive
  object={scene}
  scale={scaleFactor}
  position={[x, y + lift * scaleFactor, z]}
/>
```

## Scene Pipeline

**Workflow:**
```
Download packs (free) -> Assemble in Blender -> Export GLB -> Load in R3F
```

### Asset Sources (CC0 / Free)

| Source | URL | Best For |
|--------|-----|----------|
| KayKit | itch.io/kaylousberg | Town, dungeon, furniture |
| Kenney | kenney.nl/assets | Clean low-poly props |
| Quaternius | quaternius.com | Characters, buildings |
| Sketchfab | sketchfab.com | Specific items (check license) |

Search terms: "low poly town", "stylized furniture", "dungeon pack", "office interior"

### Scenes Needed

**1) Town Square (Day/Night)**
- Central round table
- 4-6 backdrop buildings
- Street lamps (4x)
- Benches, fountain, props

**Packs:** KayKit Medieval Builder, KayKit City Builder

**2) Mafia Lair**
- Dark basement/warehouse
- Table + chairs
- Boxes, barrels, crates
- Single hanging lamp

**Packs:** KayKit Dungeon, KayKit Furniture

**3) Detective Office**
- Desk with lamp
- Filing cabinets
- Window with blinds
- Papers, props

**Packs:** KayKit Furniture, generic office assets

**4) Doctor Scene**
- Small clinic corner or medical room
- Exam table or cot
- Cabinet with supplies
- Simple wall light or lamp

**Packs:** KayKit Furniture, Kenney props (medical if available)

### Blender Assembly

1. Import assets (GLB/FBX)
2. Arrange scene - position props, set scale
3. Adjust materials to match palette + plastic look
4. Set origin - scene center at (0, 0, 0), floor at y=0
5. Export GLB - include materials, no animations

**Export Settings**
- Format: glTF 2.0 (.glb)
- Include: Selected Objects
- Transform: +Y Up
- Materials: Export

### File Structure

```
viewer/public/scenes/
├── town_square.glb
├── mafia_lair.glb
├── detective_office.glb
└── doctor_office.glb
```

### R3F Integration

Scenes load in `Stage.jsx` based on `sceneKind` prop:
- `sceneKind="town"` -> town_square.glb (day/night via lighting)
- `sceneKind="mafia"` -> mafia_lair.glb
- `sceneKind="detective"` -> detective_office.glb
- `sceneKind="doctor"` -> doctor_office.glb

Stage auto-centers + scales scene GLBs to a target width, then applies an optional offset.
Tune `SCENE_TARGET_WIDTH` and `SCENE_OFFSETS` in `viewer/src/components/Stage.jsx`.

## Consistency Checklist (Required)

- Keep generated textures (Textured Mesh enabled) for characters.
- Override material properties only (metalness=0, roughness=0.5, clearcoat=0.05).
- Normalize scale (humanoids ~1.7m).
- Pivot at feet (characters) and base (props).
- Re-center models to origin.
