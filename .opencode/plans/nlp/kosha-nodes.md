# Kosha Nodes: Bhave Processes + Subanta Quantities

All kosha nodes that represent domain knowledge split into two pada types. After the
varga restructure, every node declares its samanya via `vishesa` edge — inheriting shared
slokas from the parent. Only node-specific slokas remain on the leaf.

---

## IK processes (ik-karma vishesa)

```
kosha reach-target
  "ik-karma-vishesa"
  "ik-ahara gati-kriya aayaama-yukta"
  shabda pos:verb signal:ik=1.0
done

kosha locate
  "ik-karma-vishesa"
  "ik-ahara aayaama-yukta bindu-swarupa"
  shabda pos:verb signal:ik=1.0
done

kosha move-to
  "ik-karma-vishesa"
  "gati-kriya aayaama-yukta"
  shabda pos:verb
done

kosha rotate-by
  "ik-karma-vishesa"
  "gati-kriya kona-yukta"
  shabda pos:verb
done
```

---

## Mechanics processes (sandhi-karma vishesa)

```
kosha free-fall
  "sandhi-karma-vishesa"
  "displacement-phala gravity-yukta"
  "velocity-swarupa shunya-yukta"     -- initial-velocity IS zero
  shabda pos:verb
done

kosha projectile-motion
  "sandhi-karma-vishesa"
  "velocity-ahara kona-ahara"
  "displacement-phala"
  shabda pos:verb
done

kosha decelerate-to-rest
  "sandhi-karma-vishesa"
  "velocity-swarupa shunya-yukta"     -- final-velocity IS zero
  shabda pos:verb
done

kosha collision
  "sandhi-karma-vishesa"
  "dvaya-yukta samvega-janya"
  "asprishta-sanghat-yukta sprishta-sanghat-yukta"
  shabda collides, colliding, collision, impact / momentum-exchange-between-two-bodies
done

kosha oscillation
  "sandhi-karma-vishesa"
  "spanda-yukta kaala-yukta"
  "spanda-avdhi-yukta lola-avdhi-yukta avrti-yukta"
  shabda oscillates, vibrates, bounces, swings / periodic-simple-harmonic-motion
done
```

---

## Thermal processes (ushna-karma vishesa)

```
kosha heat-transfer
  "ushna-karma-vishesa"
  "temperature-phala energy-yukta"
  shabda pos:verb
done

kosha phase-change-boil
  "ushna-karma-vishesa"
  "temperature-phala latent-heat-yukta"
  shabda pos:verb
done

kosha phase-change-freeze
  "ushna-karma-vishesa"
  "temperature-phala latent-heat-yukta"
  shabda pos:verb
done
```

---

## Optics processes (prakaasha-karma vishesa)

```
kosha specular-reflection
  "prakaasha-karma-vishesa"
  "kona-phala mirror-yukta"
  shabda pos:verb
done

kosha refraction
  "prakaasha-karma-vishesa"
  "kona-phala refractive-index-yukta"
  shabda pos:verb
done
```

---

## Electrical processes (vidyut-karma vishesa)

```
kosha current-flow
  "vidyut-karma-vishesa"
  "current-phala ampere-yukta"
  shabda pos:verb
done

kosha charge-accumulate
  "vidyut-karma-vishesa"
  "charge-phala coulomb-yukta"
  shabda pos:verb
done
```

---

## Orbital processes (bhramana-karma vishesa)

```
kosha orbital-motion
  "bhramana-karma-vishesa"
  "orbital-velocity-phala radius-yukta mass-yukta"
  shabda pos:verb
done

kosha gravitational-attraction
  "bhramana-karma-vishesa"
  "force-phala gravitational-force-yukta"
  shabda pos:verb
done

kosha escape
  "bhramana-karma-vishesa"
  "escape-velocity-phala"
  shabda pos:verb
done
```

---

## Constraint / modal processes (niyama-karma vishesa)

```
kosha hard-constraint
  "niyama-karma-vishesa"
  "seema-kriya"
  shabda pos:modal
done

kosha soft-constraint
  "niyama-karma-vishesa"
  "niyama-yukta"
  shabda pos:modal
done

kosha capability-bound
  "niyama-karma-vishesa"
  "shakti-sthita seema-sthita"
  shabda pos:modal
done

kosha prohibition
  "niyama-karma-vishesa"
  "pratishedha-kriya pratipaksha-phala"
  shabda pos:modal
done
```

---

## Physics quantities (subanta vishesas)

```
kosha velocity
  "kramanusara-matra-vishesa"
  "vega-swarupa direction-yukta"
  "displacement-kramanusara"
  "avastha-sthita"
  shabda ...
done

kosha current
  "vidyut-matra-vishesa"
  "pravaha-swarupa"
  "ampere-yukta coulomb-yukta second-yukta"
  "voltage-yukta resistance-yukta"
  shabda current, electric-current / charge-flow-per-unit-time
done

kosha joint-speed-max
  "chalana-seema-vishesa"
  "angular-velocity-swarupa"
  "radian-per-second-matra"
  shabda joint-speed-max, omega-max / maximum-angular-speed-of-joint
done
```

---

## Preposition concepts (subanta / avyaya)

```
kosha toward         "chaturthi-vibhakti-yukta gati-kriya"    -- destination / dative
kosha from-source    "panchami-vibhakti-yukta ahara-yukta"    -- source / ablative
kosha at-location    "saptami-vibhakti-yukta avastha-yukta"   -- locative
kosha via-path       "trtiya-vibhakti-yukta krama-yukta"      -- instrumental / waypoint
kosha within-range   "saptami-vibhakti-yukta seema-sthita"    -- bounded locative
kosha by-amount      "trtiya-vibhakti-yukta matra-yukta"      -- instrumental / measure
```

---

## Quantifier concepts

```
kosha ordered-set    "krama-kriya"                  -- respectively, each, in-order
kosha pairwise       "krama-sthita dvaya-swarupa"   -- both
kosha total-set      "krama-sthita vrnda-yukta"     -- all, every
```

---

## Context/situation subanta concepts

```
kosha zero-friction-surface
  "niyama-karma-vishesa"
  "ghasana-swarupa shunya-yukta"    -- friction IS zero
  "saptami-vibhakti-yukta"
  shabda pos:adj
done

kosha horizontal-motion
  "sandhi-karma-vishesa"
  "kona-swarupa shunya-yukta"       -- angle IS zero
  shabda pos:adj
done

kosha vertical-motion
  "sandhi-karma-vishesa"
  "kona-swarupa pi-dvaya-yukta"     -- angle IS 90°
  shabda pos:adj
done

kosha initial-rest
  "sandhi-karma-vishesa"
  "velocity-swarupa shunya-yukta"   -- velocity IS zero at start
  "aarambham-sthita"
  shabda pos:adj
done
```
