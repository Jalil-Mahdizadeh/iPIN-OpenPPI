---
type: "query"
date: "2026-09-20T13:31:18.855296+00:00"
question: "explain the U pair selection in a simple language."
contributor: "graphify"
outcome: "useful"
source_nodes: ["Unlabeled selection", "Unlabeled controls", "build_panels.py"]
---

# Q: explain the U pair selection in a simple language.

## Answer

Expanded from original query via graph vocabulary: [unlabeled, selection, context, exclusions].
U means unlabeled: whether that target-protein pair interacts is unknown, and some U pairs may be real interactions. For each target the source is reviewed human UniProt proteins with protein-level existence evidence. Remove the target itself, nominated positives, interaction/association partners identified in the checked IntAct/UniProt records (and explicit literature exclusions in the original panels), target-partner pairs already in checked training/development P or U arrays by accession or exact sequence, and identical-sequence duplicates.
For each known positive partner, choose 100 other eligible proteins: 50 from its broad cellular compartment with the same presence/absence of an annotated membrane-spanning segment, and 50 from the broader eligible human pool without those location/membrane restrictions. All 100 must be half to twice the positive partner's sequence length. Matching is to the positive partner, not the target.
Example: for KRAS-RAF1, RAF1 supplies matching characteristics, but the resulting U rows are KRAS-X, KRAS-Y, etc. Three positive partners yield 300 U pairs; ERN1's four yield 400; all twelve yield 3700. Selection follows a fixed repeatable SHA-256 order without model scores. A U protein appears at most once within a target panel, though it may recur under a different target. The matching controls simple length/location differences; database screening cannot establish noninteraction.
Source: example/KRAS/README.md:19 and example/twelve_target_comparison_v1/build_panels.py:218-282; graph entry points Unlabeled selection and Unlabeled controls.


## Outcome

- Signal: useful

## Source Nodes

- Unlabeled selection
- Unlabeled controls
- build_panels.py