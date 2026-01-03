# Scene Pipeline

Build scenes from free asset packs instead of generating props.

## Workflow

```
Download packs (free) → Assemble in Blender → Export GLB → Load in R3F
```

## Asset Sources (CC0 / Free)

| Source | URL | Best For |
|--------|-----|----------|
| KayKit | itch.io/kaylousberg | Town, dungeon, furniture |
| Kenney | kenney.nl/assets | Clean low-poly props |
| Quaternius | quaternius.com | Characters, buildings |
| Sketchfab | sketchfab.com | Specific items (check license) |

**Search terms:** "low poly town", "stylized furniture", "dungeon pack", "office interior"

## Scenes Needed

### 1. Town Square (Day/Night)
- Central round table
- 4-6 backdrop buildings
- Street lamps (4x)
- Benches, fountain, props

**Packs:** KayKit Medieval Builder, KayKit City Builder

### 2. Mafia Lair
- Dark basement/warehouse
- Table + chairs
- Boxes, barrels, crates
- Single hanging lamp

**Packs:** KayKit Dungeon, KayKit Furniture

### 3. Detective Office
- Desk with lamp
- Filing cabinets
- Window with blinds
- Papers, props

**Packs:** KayKit Furniture, generic office assets

## Blender Assembly

1. **Import assets** (GLB/FBX)
2. **Arrange scene** - position props, set scale
3. **Adjust materials** - match style_bible.md (plastic look, palette colors)
4. **Set origin** - scene center at (0, 0, 0), floor at y=0
5. **Export GLB** - include materials, no animations

### Export Settings
- Format: glTF 2.0 (.glb)
- Include: Selected Objects
- Transform: +Y Up
- Materials: Export

## File Structure

```
viewer/public/scenes/
├── town_square.glb
├── mafia_lair.glb
└── detective_office.glb
```

## R3F Integration

Scenes load in `Stage.jsx` based on `sceneKind` prop:
- `sceneKind="town"` → town_square.glb (day/night via lighting)
- `sceneKind="mafia"` → mafia_lair.glb
- `sceneKind="detective"` → detective_office.glb

Stage auto-centers + scales scene GLBs to a target width, then applies an optional offset.
If a scene feels too big/small or misaligned, adjust:
- `SCENE_TARGET_WIDTH` and `SCENE_OFFSETS` in `viewer/src/components/Stage.jsx`

## Style Consistency

Per style_bible.md:
- Scale: 1 unit = 1 meter
- Materials: metalness=0, roughness=0.5
- Colors: use palette hex values
- No shadows in export (handled by lighting)

## Tips

- **Start simple** - basic blockout first, add detail later
- **Reuse assets** - same props across scenes
- **Test early** - export and load in viewer before polishing
- **Keep poly count low** - stylized look doesn't need high detail
