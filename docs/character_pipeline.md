### Asset Pipeline (Practical)
- **Target:** stylized mesh humanoid toy with a Roblox-adjacent silhouette:
  - Surface: matte hard plastic, solid colors
  - Geometry: blocky, low-poly with sharp corners
  - Proportions: big head (about 1/3 height), boxy body, distinct limbs
  - Silhouette: clean, simple, readable at thumbnail size
  - Materials: no gradients, no photo-textures, no micro-detail, no round bevels
- **API:** fal.ai (Hunyuan3D v2 for characters)
- **Input:** clean 2D reference image (front or 3/4 view, clear silhouette)
- **Output:** `.glb` for R3F
- **Post-process:** normalize scale (~1.7 units tall), pivot at feet, use generated textures/materials as-is (adjust roughness/metalness only if too shiny)

**Prompt**
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
**Prompt 2**
```
Transform to 3D plastic toy reference: Roblox-adjacent blocky character,
  big head (about 1/3 height), boxy body, distinct limbs,
  A-pose (arms 30° from body), matte hard plastic, solid colors,
  white background, frontal view, flat lighting.
  Preserve character's iconic features and colors.
  NO realistic textures, NO gradients, NO fine detail, NO round bevels.
```

**Hunyuan3D v2 settings (fal.ai)**
| Setting | Value | Notes |
|---------|-------|-------|
| Image Input | Clean 2D reference (e.g., Nano Banana output) | Required |
| Num Inference Steps | 50 | Higher = more detail |
| Guidance Scale | 7.5 | Use 9-10 if fidelity is low |
| Octree Resolution | 256 | 512 for more detail, 128 for blockier |
| Textured Mesh | Enabled | Always keep enabled - preserves colors from reference image |

Workflow:
1) Run with defaults.
2) If too smooth, increase Octree Resolution.
3) If off-model, increase Guidance Scale.
4) If too detailed, reduce Octree Resolution.

**Post-process in viewer**
- Normalize pivot to floor using bounding box min.y.
- Normalize scale to ~1.7 units tall.
- Keep generated textures (colors), but override material properties in code (metalness=0, roughness=0.5, clearcoat=0.05) for consistent plastic look across all models.

Example snippet (TestModel/Character model loader):
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
