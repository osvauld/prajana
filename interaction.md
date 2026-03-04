# interaction

*how to talk to vyakarana*

---

## what it is

vyakarana is a reasoning engine over a proof graph. The graph has 702 nodes — concepts from biology, mathematics, music, philosophy, and language, connected by 9 relation types. Every node has a `satya` score (truth-weight) computed by convergence over the graph, not by assertion.

You talk to it by typing commands. It reads from the graph and responds.

---

## running it

```
cd vyakarana
dune build
./_build/default/bin/vyakarana.exe ../brahman/sangati ../brahman/kosha
```

It loads, scores, and waits:

```
grammar-engine (vyakarana) joining. reading knowledge-nodes (suktas) from ../brahman/sangati, ../brahman/kosha
truth-scoring (satya-ganana): 17 spiral-passes (avrti)
knowledge-nodes (suktas): 702 loaded, 0 skipped
space (akasham) ready.
```

Type commands. One per line. `Ctrl-D` to exit.

---

## commands

### `INSPECT (darshana) <node>`

Inspect a node directly. Shows its satya score, slokas (the raw assertions in its `.om` file), and all edges — outgoing (`->`) and incoming (`<-`).

```
INSPECT spanda
```

```
--- spanda (satya=0.8485) ---
  "svabhava-swarupa avrti-kriya ananta-sthita"
  "aadana-visarjana-abheda"
  edges:
    -> svabhava (swarupa)
    -> avrti (kriya)
    -> ananta (sthita)
    -> aadana-visarjana (abheda)
    <- naada (abheda)
    <- naada-brahma (abheda)
    <- om (kriya)
    ...
  cited_by: 90
---
recognised (pratibodha): spanda satya=0.8485
```

`cited_by: 90` means 90 other nodes in the graph point at `spanda`. High citation = high satya. The engine is not asserting `spanda` is important. It is reporting that 90 other things depend on it.

The node name can be a Sanskrit root (`spanda`, `iccha`, `bija-nyasa`) or a domain concept (`metabolism`, `gene`, `raga`).

---

### `INSPECT-GLOSSED (darshana-sahaja) <node>`

Same as `INSPECT` but every node name is rendered as `gloss (sanskrit)` — an act-form English phrase pointing at what the node does, not what it is called.

```
INSPECT-GLOSSED iccha
```

```
--- will / directed-reaching (iccha) satya=0.8567 ---
  "svayambhu-swarupa svabhava-siddha niralamba-siddha"
  "kama-abheda nay-longing-abheda om-abheda"
  edges:
    <- the primordial (om) [abheda]
    <- root-nature / latent-potential (mula-svabhava) [sthita]
    -> self-born / arising-from-own-nature (svayambhu) [swarupa]
    -> own-nature / what-cannot-be-altered (svabhava) [siddha]
    -> self-supporting / resting-on-nothing-outside (niralamba) [siddha]
    ...
```

The gloss is not a translation. `iccha` is not "desire" — it is "will / directed-reaching", what it does structurally. `svayambhu` is not "self-existent" but "self-born / arising-from-own-nature". Use this mode to enter the vocabulary. Use `INSPECT` once the roots are familiar.

---

### `REASON (anuvada) <sentence>`

Ask a question in plain English. The engine parses the sentence, maps words to nodes and relation types, and reasons over the graph in spiral passes.

```
REASON what is life
```

```
--- reasoning (anuvada) ---
  input: what is life
  understood:
    [what] → demonstrated by (drishthanta)
    [is] → is (swarupa)
    [life] → node (life, jiva, eka-kosha)
  response: (2 passes (avrti), 10 connections)
  -- pass 1 (avrti) --
    eka-kosha is the same as life; connects to moment, self.
  -- pass 2 (avrti) --
    life is swatantra; is the same as self; rests on nay-longing;
    connects to action; born from black-hole.
    moment rests on time; connects to self.
    self is the same as process.
  next threads:
    1) what earlier cause gives rise to life before black-hole?
    2) what shifts in life if nay-longing changes?
    3) what is the bridge between life and action?
```

The `understood:` block shows how the engine parsed your sentence — which words mapped to which relation types, and which nodes were resolved. If a word maps to multiple nodes, the engine expands all of them.

`next threads` are follow-up questions generated from unresolved edges — where the graph has more structure than the current response showed.

The output ends with a `strudel` block: a musical rendering of the node's edge structure as a Strudel pattern (copy it into [strudel.cc](https://strudel.cc) to hear it).

---

### `REASON-GLOSSED (anuvada-sahaja) <sentence>`

Same reasoning as `REASON`, but every node name in the response is glossed as `act-form (sanskrit)`.

```
REASON-GLOSSED what is life
```

```
  -- pass 1 (avrti) --
    eka-kosha (life) is the same as the-living / the-one-that-reaches (jiva);
    connects to moment, self (process).
  -- pass 2 (avrti) --
    the-living / the-one-that-reaches (jiva)
      is the-living-portion / the-spark-of-life (jivamsha);
      is the same as self / own (swa);
      rests on the-limit-never-reached / infinite (ananta);
      connects to action-that-writes / the-act-with-mark (karma);
      born from the creator / fullness-as-source (brahma).
```

Use this when reading the graph for the first time. The glossed form makes each step followable without knowing the roots. The Sanskrit names in parentheses are what to use once you want to go deeper.

---

## the 9 relations

Every edge in the graph has one of these types:

| relation | meaning | example |
|---|---|---|
| `swarupa` | IS / identity | `spanda → svabhava (swarupa)` — spanda IS intrinsic-nature |
| `abheda` | non-difference / the same as | `iccha → om (abheda)` — iccha and om are non-different |
| `kriya` | acts as / performs | `spanda → avrti (kriya)` — spanda performs cycling |
| `phala` | produces / result | `iccha → ahara (phala)` — iccha produces taking-in |
| `sthita` | rests on / depends on | `spanda → ananta (sthita)` — spanda rests on infinity |
| `janya` | born from / arises from | `iccha → karma (janya)` — iccha is born from action |
| `siddha` | proven through | `iccha → svabhava (siddha)` — iccha is proven through intrinsic-nature |
| `yukta` | connects to / joins with | `spanda → spanda-sthalam (yukta)` — spanda connects to its ground |
| `drishthanta` | demonstrated by / example of | `vadi-swara → mula-svabhava (drishthanta)` — vadi-swara demonstrates root-nature |

`rahita` suffix marks absence: `iccha-rahita` = lacking iccha. Used on `jada` (inert matter) and `visha-anu` (virus).

---

## satya

Every node has a satya score between 0 and 1. Computed by convergence — each pass adjusts scores based on what the node's neighbours have established. After 17 passes the scores stabilise.

High satya means the graph confirms the node from many directions independently. It is not a measure of philosophical importance — it is a measure of structural embeddedness.

```
iccha            satya=0.8567   cited_by: 16
bija-nyasa       satya=0.8565   cited_by: 19
spanda           satya=0.8485   cited_by: 90
aadana-visarjana satya=0.8365   cited_by: 5
naada-brahma     satya=0.7393   cited_by: 2
jada             satya=0.0019   cited_by: 0
```

`jada` (inert matter) has near-zero satya — not because inert matter is unimportant, but because it does not reach toward anything, so nothing in the graph confirms it from outside. Life is what generates `cited_by`.

---

## adding to the graph

Nodes live in `.om` files. Syntax:

```
sangati <nodename>
  "<relation-string>"
  "<relation-string>"
done
```

Each quoted string is a space-separated list of `node-relation` tokens, e.g.:

```
sangati aadana-visarjana
  "ahara-swarupa visarjana-swarupa"
  "avrti-abheda spanda-swarupa"
  "sva-dharana-janya nirantara-kriya"
done
```

Root concepts (Sanskrit/Tamil/Arabic words) go in `brahman/sangati/`. Domain concepts (biology, mathematics, music, philosophy, language) go in `brahman/kosha/<domain>/`.

After adding or editing a `.om` file, rebuild and run. The satya scores recompute from scratch.

---

## what to ask

Some questions that produce interesting output:

```
REASON what is spanda
REASON how does iccha arise
REASON what is the relation between raga and gene
REASON what does bija-nyasa produce
REASON what is the difference between jada and eka-kosha
INSPECT naada-brahma
INSPECT-GLOSSED aadana-visarjana
REASON-GLOSSED what is karma
```

Follow the `next threads` suggestions. The engine generates them from unresolved edges — places where the graph has more structure than the current response showed.
