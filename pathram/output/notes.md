# Notes

## Step 3.0 implementation differs from original plan: (1) No individual bhasha greeting nodes — shabda signals instead (english-grammar-signals.shabda). (2) No sambodhana-yukta in visheshanam-ring needed — detection via shabda lookup not graph walk. (3) emit-triples emits actual signal degree (sambodhana/abhisambodhana/aamantrana) not just sambodhana. (4) vacaka and addressee connected to chala-apeksha and sthira-apeksha respectively. (5) Vaisheshika padarthas formalized as sangati/padartha/ — thing/some/something now point to real roots.

## Three new om query tools: (1) om classify <node> — edge affinity analysis, suggests sthalam. (2) om ungrouped — all top-level sangati nodes grouped by suggested sthalam. (3) om sthalam <name> — current + candidate members by edge affinity. All static analysis, no server needed.

## restructure_sangati.py script in scripts/ — copies sangati/ to sangati2/ with sub-bucket mapping, dry-run by default, --apply to execute. Mapping dict defines node→sub-bucket. Can be reused for future restructuring.

## pathram math should emit the pipeline function from the graph architecture (krama chain + janya/phala) not from static tantra file parsing. walk pipeline-construct krama 7 gives the layers. Each layer's janya/phala gives the type signature. This makes the math description self-derived.
