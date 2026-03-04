# Geometry Plan

## Principle
Geometric primitives are structural truths — they belong in `brahman/sangati/`.
They are not math concepts or physics concepts. Math, physics, chemistry, biology
all instantiate them. The sangati nodes carry no domain tags.

Derived shapes (cylinder, cone, triangle) live in `brahman/kosha/math/`.
Rendered approximations (mesh, vertex, fragment) live in `brahman/kosha/3d/`.
Domain nodes (orbit, covalent-bond, dna) gain back-reference edges to sangati geometry.

## Key Principles
- `kshetra` (already in sangati) = boundary. Every thing is a bounded region of akasham.
- `aayaama` (already in sangati, needs deepening) = dimension count.
- `tala` = flatness / 2D nature. Not infinite plane — that is handled by kshetra.
- Math does not mention rendering. Rendering references math.

---

## Layer 1 — Sangati (structural truths, no domain tags)

### aayaama — deepen existing `brahman/sangati/aayaama.om`
Currently: `ananta-swarupa antarvidya-yukta purna-abheda brahma-sthita darshana-kriya`
Add:
- `akasham-yukta` — aayaama defines akasham's reach
- `bindu-sthita` — a bindu has aayaama=0
- `rekha-sthita` — rekha has aayaama=1
- `tala-sthita` — tala has aayaama=2
- `akasham-sthita` — akasham has aayaama=3 (in manifest form)
Domain drishthanta (existing nodes):
- `vector-drishthanta` — math: dimension of a vector space
- `degrees-of-freedom-drishthanta` — physics: phase space dimensions
- `body-plan-drishthanta` — biology: anterior-posterior, dorsal-ventral, left-right

### akasham — new `brahman/sangati/akasham.om`
What: the unbounded field of extension, n-dimensional, prior to any coordinate system.
Essence: not a shape — the precondition for shape. Pure potential of extension.
In Pancha Bhuta: the first and most subtle element, from which all others arise.
Edges:
- `kshetra-swarupa` — akasham IS a field (unbounded)
- `aayaama-yukta` — qualified by dimension count
- `ananta-sthita` — situated in infinity
- `nirantara-sthita` — continuous
- `panchabhootam-sthita` — first of the five elements
- `shunya-poorva` — arises after shunya (emptiness before extension)
Drishthanta (existing nodes):
- `space-drishthanta` — physics/space.om
- `world-space-drishthanta` — 3d/world-space.om

### bindu — new `brahman/sangati/bindu.om`
What: the point. Zero extent. Pure position in akasham. Seed of all geometry.
In tantric thought: the point of creative potential before expansion (Kashmir Shaivism).
Edges:
- `kshetra-swarupa` — bounded field at minimum (zero extent)
- `akasham-sthita` — situated in akasham
- `aayaama-shunya-sthita` — has zero aayaama
- `shunya-abheda` — non-different from zero in extent
Drishthanta (existing nodes):
- `atom-drishthanta` — physics: particle position, nuclear center
- `cell-drishthanta` — biology: cell as a located entity
- `seed-drishthanta` — kosha: seed as point of origin

### rekha — new `brahman/sangati/rekha.om`
What: the line. Two bindus connected by the shortest path. Has direction and length, no width.
Edges:
- `kshetra-swarupa` — bounded field (between two bindus)
- `akasham-sthita` — situated in akasham
- `bindu-yukta` — defined by bindus
- `tantu-abheda` — non-different from thread (tantu already in sangati)
- `vector-abheda` — a directed rekha IS a vector
- `sambandha-swarupa` — a rekha IS a connection between two bindus
Drishthanta (existing nodes):
- `covalent-bond-drishthanta` — chemistry: the line between atoms
- `dna-drishthanta` — biology: the strand
- `alpha-helix-drishthanta` — biology: axis of the helix
- `polymer-drishthanta` — chemistry: the chain

### tala — new `brahman/sangati/tala.om`
What: flatness. The principle of two-dimensional extension. Not an infinite plane —
that would be akasham with aayaama=2. Tala is the quality of being flat, of lying
in one plane. A trikona is tala-sthita. The surface of a table is tala-sthita.
Edges:
- `akasham-sthita` — situated in akasham
- `aayaama-dvaya-sthita` — has two aayaamas
- `kshetra-swarupa` — a bounded flat region
- `rekha-yukta` — tala is spanned by rekhas
Drishthanta (existing nodes):
- `matrix-drishthanta` — math: a matrix is a tala of values
- `membrane-drishthanta` — biology: cell membrane as a flat surface
  (note: membrane.om does not exist yet — skip or create)

### vrtta — new `brahman/sangati/vrtta.om`
What: the circle. All points in tala at equal distance from one bindu (the kendra).
The closed curve. Root of gola (3D) and vrtta-stambha (cylinder, in kosha/math/).
Edges:
- `kshetra-swarupa` — a bounded region (or its boundary)
- `tala-sthita` — situated in a plane
- `bindu-yukta` — defined by a center bindu + equal distance
- `avrti-abheda` — non-different from repetition/cycle (avrti in sangati)
- `tantu-abheda` — the circle as a closed thread
Drishthanta (existing nodes):
- `orbit-drishthanta` — physics: orbital path
- `avrti-drishthanta` — sangati: cycle, return

### gola — new `brahman/sangati/gola.om`
What: the sphere. All points in akasham at equal distance from one bindu (the kendra).
The 3D vrtta. The most symmetric closed surface in akasham.
Edges:
- `kshetra-swarupa` — a bounded region (or its surface)
- `akasham-sthita` — situated in akasham (not just tala)
- `vrtta-janya` — born from vrtta (vrtta rotated around its diameter)
- `bindu-yukta` — defined by center bindu + equal distance
- `purna-abheda` — non-different from fullness (most symmetric, no preferred direction)
Drishthanta (existing nodes):
- `atom-drishthanta` — physics: electron cloud, nuclear radius
- `cell-drishthanta` — biology: spherical cell body
- `wave-drishthanta` — physics: spherical wavefront

---

## Layer 2 — Kosha/math (derived shapes)

### trikona — new `brahman/kosha/math/trikona.om`
What: triangle. Three bindus, three rekhas, minimum enclosure of area in tala.
The simplest polygon. Rigid under force (no internal degrees of freedom).
Why fundamental: every surface can be triangulated. The GPU rasterizes triangles.
Edges:
- `kshetra-swarupa tala-sthita` — a flat bounded region
- `rekha-traya-sthita` — three rekhas
- `bindu-traya-sthita` — three bindus
- `domain-math-sthita` — belongs to math domain
Drishthanta:
- `bridge-structure-drishthanta` — physics: structural rigidity
- `trigonal-molecule-drishthanta` — chemistry: BF3, SO3 geometry

### vrtta-stambha — new `brahman/kosha/math/vrtta-stambha.om`
What: cylinder. A vrtta swept along a rekha. Every cross-section is a circle.
Edges:
- `kshetra-swarupa akasham-sthita`
- `vrtta-janya rekha-sthita`
- `domain-math-sthita`
Drishthanta:
- `alpha-helix-drishthanta` — biology
- `polymer-drishthanta` — chemistry
- `solenoid-drishthanta` — physics

### shankha — new `brahman/kosha/math/shankha.om`
What: cone. A vrtta shrinking along a rekha to a single bindu at the apex.
Edges:
- `kshetra-swarupa akasham-sthita`
- `vrtta-janya bindu-phala rekha-sthita`
- `domain-math-sthita`
Drishthanta:
- `conic-section-drishthanta` — math
- `funnel-drishthanta` — biology/chemistry

---

## Layer 3 — Kosha/3d (rendered approximations)

### mesh — new `brahman/kosha/3d/mesh.om`
What: a collection of trikona that approximates a mathematical shape (gola, vrtta-stambha).
The bridge between sangati geometry and rendered pixels.
Edges:
- `trikona-swarupa akasham-sthita`
- `gola-abheda vrtta-stambha-abheda` (approximates these)
- `domain-3d-sthita`

### vertex — new `brahman/kosha/3d/vertex.om`
What: a bindu in rendered space, carrying additional attributes: position, color, normal, uv.
Edges:
- `bindu-swarupa domain-3d-sthita`
- `normal-yukta` — carries surface normal (normal.om exists in math)

### rasterization — new `brahman/kosha/3d/rasterization.om`
What: the kriya that converts trikona (continuous math) into fragments (discrete pixels).
The bridge between akasham geometry and the screen raster grid.
Takes each projected trikona, finds which screen pixels fall inside it,
interpolates vertex attributes across those pixels via barycentric coordinates.
Why triangles: three points always define exactly one plane. Any polygon splits into
triangles. Barycentric interpolation is exact and unambiguous for triangles.
The GPU is built around this single kriya — it is the atom of rendering.
Edges:
- `kriya-swarupa domain-3d-sthita`
- `trikona-ahara` — takes trikona as input
- `fragment-phala` — produces fragments as output
- `bindu-janya` — each fragment is a bindu born from trikona
- `tala-sthita` — operates in screen-space tala (2D projection)
- `prasarana-abheda` — IS a propagation (from 3D akasham to 2D screen)
Drishthanta: none — rasterization is itself the domain-specific instantiation

### fragment — new `brahman/kosha/3d/fragment.om`
What: a pixel-sized piece of a trikona after rasterization. The smallest unit of rendered output.
Carries interpolated attributes — color, depth, normal, texture coordinates — from the
three vertices of its parent trikona via barycentric weights.
Edges:
- `trikona-janya domain-3d-sthita`
- `bindu-abheda` — a fragment is a screen-space bindu
- `rasterization-janya` — born from rasterization kriya
- `matra-sthita` — it is the smallest unit of rendered output

---

## Layer 4 — Back-references in existing domain nodes

Add edges to existing nodes (do not rewrite — add only):
- `physics/orbit.om` → add `vrtta-abheda`
- `physics/wave.om` → add `gola-drishthanta` (spherical wavefront)
- `chemistry/covalent-bond.om` → add `rekha-abheda`
- `biology/dna.om` → add `rekha-drishthanta`
- `biology/alpha-helix.om` → add `vrtta-stambha-drishthanta`
- `kosha/cell.om` → add `gola-drishthanta`

---

## Layer 5 — Time nodes

### physics/time.om — new
What: time as physics uses it. Counted vibrations of a reference oscillator.
Observer-dependent (special + general relativity).
Edges:
- `kaala-sthita` — grounded in kaala (pure sequence, already in sangati)
- `spanda-matra-abheda` — time IS counted vibration
- `kshetrajna-yukta` — observer-dependent
- `matra-sthita` — it is a measure
- `second-yukta` — SI unit is the second (second.om exists)
- `velocity-yukta` — depends on relative velocity (time dilation)
- `domain-physics-sthita`

### computation/concepts/clock-cycle.om — new
What: the processor clock. One oscillation of the CPU crystal oscillator.
Every instruction executes in N clock cycles. CS time is clock cycles, not seconds.
Edges:
- `kaala-sthita` — grounded in kaala
- `spanda-abheda` — IS a vibration (crystal oscillator)
- `avrti-abheda` — IS a cycle
- `matra-sthita` — it is the CS unit of time
- `frequency-yukta` — measured in Hz (GHz for modern CPUs)
- `domain-cs-sthita`

---

## Status — Sangati nodes completed

- `sama` — written ✓
- `dura` — written ✓
- `sama-dura` — written ✓ (also: `samakalana` renamed to `sama-kalana`)
- `aayaama` — deepened ✓
- `akasham` — written ✓
- `bindu` — written ✓
- `rekha` — written ✓
- `tala` — written ✓
- `vrtta` — written ✓
- `gola` — written ✓

Back-references added to: `vector`, `orbit`, `covalent-bond`, `dna`, `cell`, `alpha-helix`, `wave`

## Order of execution — remaining

1. Write `trikona` in kosha/math
2. Write `vrtta-stambha` in kosha/math
3. Write `shankha` in kosha/math
4. Write `mesh` in kosha/3d
5. Write `vertex` in kosha/3d
6. Write `rasterization` in kosha/3d
7. Write `fragment` in kosha/3d
8. Write `physics/time.om`
9. Write `computation/concepts/clock-cycle.om`
10. Remaining back-references (wave, alpha-helix)
8. Write `trikona` in kosha/math
9. Write `vrtta-stambha` in kosha/math
10. Write `shankha` in kosha/math
11. Write `mesh`, `vertex`, `rasterization`, `fragment` in kosha/3d
12. Write `physics/time.om`
13. Write `computation/concepts/clock-cycle.om`
14. Add back-references to existing domain nodes
