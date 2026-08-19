"""Exact constants frozen by DEC-0028 and activated by DEC-0030."""

from __future__ import annotations

from pathlib import Path


PROTOCOL_ID = "model_governance_and_baseline_training_protocol_v1"
STAGE_ID = "stage1_model_execution_v1"
PROTOCOL_CONFIGURATION_SHA256 = "3b001efa026a57d2937b041c26217ff87e3fdcda3ca1553d851bf347330333d5"
MODEL_SIF_SHA256 = "c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91"
ENDPOINTS_SHA256 = "4d1962734552a6d847da64e95a7fb7fc2cde07268ca5b043f5dc5e74fa46a43e"
PARTITIONS_SHA256 = "66db8cd59e7cb8cf06ff3ad785448dfc7d5fdd24643811946246d129b0bd8a67"
COMPONENTS_SHA256 = "2742c339783b26826ed08e03198b9fce13e540c9e22b8bae90310f7c0e4ede0d"
POSITIVE_SHA256 = "4ac95c75051c7149e16e8f9a14689d1ea07f8c4e2b892a890b8a2c57ef66d499"
UNLABELED_SHA256 = "d562f860d93beb3b01ac4d658ed9e7bab41a8271baffe0176061ccc9a4a7adc7"
STRATA_SHA256 = "b8e4247ce934d837477513b322af008413ac8d61fa95ccedd16fe2712c1d6427"

ENDPOINTS_PATH = Path(
    "data/canonical/benchmark_eligibility_and_sequence_component_audit_v1/"
    "eligible_reference_sequences/part-00000.parquet"
)
PARTITIONS_PATH = Path(
    "data/canonical/final_benchmark_component_split_v1/"
    "endpoint_partition_assignments/part-00000.parquet"
)
COMPONENTS_PATH = Path(
    "data/canonical/final_benchmark_component_split_v1/"
    "component_partition_assignments/part-00000.parquet"
)
POSITIVE_PATH = Path(
    "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
    "positive_pairs/part-00000.parquet"
)
UNLABELED_PATH = Path(
    "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
    "unlabeled_pairs/part-00000.parquet"
)
STRATA_PATH = Path(
    "data/canonical/pair_level_pu_r_benchmark_artifacts_v1/training/"
    "sampling_strata/part-00000.parquet"
)

MODEL_CACHE_ROOT = Path("artifacts/cache/models") / PROTOCOL_ID
EMBEDDING_ROOT = Path("artifacts/embeddings") / PROTOCOL_ID
RUN_ROOT = Path("artifacts/runs") / STAGE_ID
CHECKPOINT_ROOT = Path("artifacts/checkpoints") / STAGE_ID
VALIDATION_ROOT = Path("artifacts/validation/model_execution") / STAGE_ID
MODEL_CUSTODY_MANIFEST_PATH = VALIDATION_ROOT / "MODEL_CUSTODY_MANIFEST.json"
MODEL_CUSTODY_MANIFEST_SHA256 = "a32399a1bdff8b56ff15509ec922e58f78a0e0bf6b860093db2f4952f48bbffe"
MODEL_RUNTIME_REPORT_PATH = VALIDATION_ROOT / "MODEL_RUNTIME_QUALIFICATION_REPORT.json"
MODEL_RUNTIME_REPORT_SHA256 = "a96ceb38d5beca8e3c3d640f99341111ed477e9a39e61494e42555c3d17020ec"

CANDIDATES = {
    "esm2_150m": {
        "repository": "facebook/esm2_t30_150M_UR50D",
        "revision": "a695f6045e2e32885fa60af20c13cb35398ce30c",
        "checkpoint_sha256": "c3f1da8aea53bddd32c246c86168c23b9fd72341fb9db9a94436f855f5053566",
        "hidden_size": 640,
        "layers": 30,
    },
    "esm2_650m": {
        "repository": "facebook/esm2_t33_650M_UR50D",
        "revision": "08e4846e537177426273712802403f7ba8261b6c",
        "checkpoint_sha256": "a08adabb949fa67ad3c14b509d04fd60368b35007b0095e3358f81200c4f4db0",
        "hidden_size": 1280,
        "layers": 33,
    },
}

SEEDS = (20260803, 20260817, 20260831)
TRAINING_SALT = "ipin-openppi-model-training-v1"
HASH_BASELINE_SALT = "ipin-openppi-pu-r-baseline-v1"
HASH_BASELINE_SEED = "20260803"
MAX_RESIDUES = 1022
OVERLAP_RESIDUES = 128
STRIDE_RESIDUES = 894
MAX_RESIDUE_TOKENS_PER_BATCH = 4096
TRAIN_ENDPOINTS = 11_900
TOTAL_ENDPOINTS = 17_000
POSITIVE_ROWS = 16_799
UNLABELED_ROWS = 2_000_000
PASSES = 5
BATCH_COMPARISONS = 4096
STEPS_PER_PASS = 489
TOTAL_STEPS = 2445
WARMUP_STEPS = 123
FINAL_LR_FRACTION = 0.1
SWAP_TOLERANCE = 1e-6
REPEAT_FRACTION = 0.01
REPEAT_TOLERANCE = 1e-6
PARAMETER_CEILING = 2_000_000

LINEAR_RECIPES = {
    "linear_lr3e-4": {"learning_rate": 3e-4, "weight_decay": 1e-4, "dropout": 0.0},
    "linear_lr1e-3": {"learning_rate": 1e-3, "weight_decay": 1e-4, "dropout": 0.0},
}
NONLINEAR_RECIPES = {
    "nonlinear_conservative": {"learning_rate": 3e-4, "weight_decay": 1e-4, "dropout": 0.1},
    "nonlinear_default": {"learning_rate": 1e-3, "weight_decay": 1e-4, "dropout": 0.1},
    "nonlinear_no_dropout": {"learning_rate": 1e-3, "weight_decay": 1e-5, "dropout": 0.0},
}
FAMILIES = {
    "lightweight_esm2_150m_linear": {"candidate_id": "esm2_150m", "recipes": LINEAR_RECIPES},
    "esm2_650m_linear_ablation": {"candidate_id": "esm2_650m", "recipes": LINEAR_RECIPES},
    "esm2_650m_nonlinear_no_gate_ablation": {
        "candidate_id": "esm2_650m",
        "recipes": NONLINEAR_RECIPES,
    },
    "esm2_650m_partner_gated_primary": {
        "candidate_id": "esm2_650m",
        "recipes": NONLINEAR_RECIPES,
    },
}

ALLOWED_SCIENTIFIC_INPUTS = {
    ENDPOINTS_PATH.as_posix(),
    PARTITIONS_PATH.as_posix(),
    COMPONENTS_PATH.as_posix(),
    POSITIVE_PATH.as_posix(),
    UNLABELED_PATH.as_posix(),
    STRATA_PATH.as_posix(),
}
FORBIDDEN_PATH_FRAGMENTS = (
    "/sealed/",
    "development_release.cms",
    "protected_candidates.cms",
    "protected_truth.cms",
    "/.private/",
)
