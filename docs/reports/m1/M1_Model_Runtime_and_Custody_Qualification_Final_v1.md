# M1 model runtime and custody qualification final report v1

**Date:** 2026-08-19

**Scope:** exact-revision ESM-2 custody and synthetic-only qualification of
`ipin-model-arm64_0.1.0.sif` before scientific Stage 1 use

**Controlling protocol:** `DEC-0028`; configuration SHA-256
`3b001efa026a57d2937b041c26217ff87e3fdcda3ca1553d851bf347330333d5`

## Result

The runtime and model-file custody gate passes. Both frozen Hugging Face
snapshots were acquired directly at the accepted immutable revisions into the
project-local cache. Each candidate contains exactly the required six regular
files, with no links and no pickle-format weight. The 150M and 650M
`model.safetensors` files match their frozen byte counts and SHA-256 digests.

`ipin-model-arm64_0.1.0.sif` was built from the accepted qualification SIF with
only three added, locally cached and hash-locked wheels: Transformers `4.55.2`,
Hugging Face Hub `0.34.4`, and Tokenizers `0.21.4`. The qualified parent already
provided the exact frozen Python, PyTorch/CUDA, NumPy, PyArrow, scikit-learn,
and Safetensors versions. The build used no network and produced a
10,656,620,544-byte ARM64 SIF with SHA-256
`c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91`.

## Production qualification

Production qualification used only a synthetic 80-residue sequence and
synthetic optimizer state. It confirmed:

- ARM64, Python/PyTorch/CUDA and every frozen package version;
- one visible NVIDIA GH200 120 GB GPU;
- offline, local-files-only Safetensors loading with remote code disabled;
- an exact checkpoint-native `EsmForMaskedLM` load with no missing,
  unexpected, or mismatched keys and no pooler;
- finite 640-dimensional FP32 and bfloat16 pooled fixtures;
- FP32 deterministic repeat maximum absolute difference `0.0`; and
- bit-exact synthetic optimizer checkpoint restart.

An early non-authoritative qualification attempt instantiated `EsmModel`
directly and correctly failed the tightened key guard because the frozen
masked-language-model head was then reported as unexpected. The accepted
loader instead instantiates the checkpoint-native `EsmForMaskedLM`, requires
every key to load, and exposes its pooler-free `.esm` residue backbone. The
accepted report contains zero key omissions and no model-loader warning.

## Independent validation

The independent validator was implemented after clean production-evidence
commit `b73df403958e0847bb799d4f90a548c99a4b3060` and does not import the
production acquisition or qualification modules. It passed 10 of 10 checks
with zero warnings and zero failures. It independently:

- rehashed the SIF and all twelve model files and reparsed both model configs;
- verified exact six-file, link-free custody and sensitive-path exclusion;
- reread architecture, parent, protocol and purpose labels from the SIF;
- loaded both exact checkpoints with Python network sockets disabled;
- obtained deterministic pooled-repeat maximum absolute difference `0.0` for
  both 150M and 650M candidates;
- confirmed finite 650M bfloat16 execution; and
- reproduced a separately implemented optimizer restart bit-exactly.

No benchmark endpoint sequence, pair row, label, development candidate,
protected candidate/truth, or private key was used by either runtime fixture.

## Frozen evidence

| Artifact | SHA-256 |
|---|---|
| Model SIF | `c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91` |
| Resolved runtime lock | `68a0086d1261ed4c6c403897e5e103ed96869652a0c04b736fa61622f241c152` |
| Qualification lock | `8af215da925736b97b00461c3a7ca11e9ee7fcc4514c3a1b777b843cf02b2635` |
| Build manifest | `e56fd8b715b662c77192c4627dd8e455901de897471deb1cb535d2357382c7fb` |
| Inspection manifest | `b5a43000a1a41452cf84c764d91b7c64eed598cd4aaa0f5485f318a3d1e620df` |
| Model custody manifest | `a32399a1bdff8b56ff15509ec922e58f78a0e0bf6b860093db2f4952f48bbffe` |
| Production qualification | `a96ceb38d5beca8e3c3d640f99341111ed477e9a39e61494e42555c3d17020ec` |
| Independent validation | `17321ee58881ba7f2a170b64ebf8411989aa1bfde18c889527bb7ee0ad2bb2ac` |

## Disposition

The exact runtime and custody snapshot satisfies every frozen prerequisite for
scientific Stage 1 use. It may be accepted only by a numbered decision. Such
acceptance does not release development, protected packages, additional model
candidates, adaptive search, negative construction, residue/interface work,
or any scientific result.
