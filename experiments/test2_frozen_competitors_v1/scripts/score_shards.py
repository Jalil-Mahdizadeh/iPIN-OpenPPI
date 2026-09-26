"""Resumable scoring of added test candidates with unmodified frozen native scorers."""
import argparse
from pathlib import Path
import signal
import time
import sys
sys.path.insert(0, "/bundle/code")
import numpy as np
import torch
from study_io import CELLS, arrays, atomic, checked_bundle, configure_cuda, now, read, record, sha, write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("method", choices=("plm", "dscript_original", "dscript_retrained"))
    parser.add_argument("--rank", type=int, default=0)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--stop-after-blocks", type=int, default=0)
    args = parser.parse_args()
    out = Path("/output")
    started = time.monotonic()
    assert 0 <= args.rank < args.workers
    config = checked_bundle()
    meta = read("/data/sequences.json")
    assert read("/bundle/endpoints.json") == meta["sha256"][:17000]
    identity = {"method": args.method, "rank": args.rank, "workers": args.workers,
                "bundle_sha256": sha("/bundle/SCORER_FREEZE.json"), "sequence_sha256": sha("/data/sequences.json"),
                "code_sha256": sha(__file__)}
    if (out / "IDENTITY.json").exists():
        assert read(out / "IDENTITY.json") == identity
    else:
        write(out / "IDENTITY.json", identity)
    if (out / "COMPLETE.json").exists():
        for item in read(out / "COMPLETE.json")["files"]:
            assert sha(out / item["path"]) == item["sha256"]
        print("Completed shard verified", flush=True)
        return
    device = configure_cuda()
    from frozen_scorer import Scorer, SCORERS
    assert list(SCORERS) == config["scorers"]
    scorer = Scorer("/bundle", device)
    if args.method == "plm":
        from native_model import learned_digest
        initial = learned_digest(scorer.model)
        assert initial == config["learned_state_sha256"]
        scorer.sequences = meta["sequence"]
        scorer.ids = np.array(meta["sha256"])
        scorer.lengths = np.array(meta["length"])
        tolerance = config["batch_tolerance"]
    else:
        from native_adapter import learned_digest
        extension = Path("/extension")
        manifest = read(extension / "COMPLETE.json")
        assert manifest["bundle_sha256"] == identity["bundle_sha256"]
        assert manifest["sequence_sha256"] == identity["sequence_sha256"]
        for item in manifest["files"]:
            assert sha(extension / item["path"]) == item["sha256"]
        if args.method == "dscript_original":
            initial = learned_digest(scorer.model)
            extra = np.load(extension / "dscript_original.npy", allow_pickle=False)
            scorer.features = torch.cat([scorer.features, torch.as_tensor(extra, device=device)])
        else:
            initial = [learned_digest(m) for m in scorer.models]
            for j, seed in enumerate((20260803, 20260817, 20260831)):
                extra = np.load(extension / f"dscript_seed_{seed}.npy", allow_pickle=False)
                scorer.values[j] = torch.cat([scorer.values[j], torch.as_tensor(extra, device=device)])
        offsets = np.r_[0, np.cumsum(meta["length"], dtype=np.int64)]
        assert np.array_equal(offsets[:17001], scorer.offsets)
        scorer.offsets = offsets
        tolerance = config.get("logit_tolerance", 1e-5)
    fixtures = arrays("/data/fixtures.npz")
    expected = arrays(f"/data/fixtures_{args.method}.npz")
    replay = scorer.scores(fixtures["a"], fixtures["b"])
    errors = {name: float(np.max(np.abs(replay[:, j] - expected[name]))) for j, name in enumerate(SCORERS)}
    assert max(errors.values()) <= tolerance, errors
    write(out / "QUALIFICATION.json", {"at_utc": now(), "passed": True, "archived_legacy_fixture_errors": errors,
          "tolerance": tolerance, "fixture_pairs": len(fixtures["a"]), "gpu": torch.cuda.get_device_name()}, exclusive=not (out / "QUALIFICATION.json").exists())
    stop = [False]
    for sig in (signal.SIGUSR1, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.__setitem__(0, True))
    files = []
    processed = 0
    for cell in CELLS:
        candidates = arrays(f"/data/candidates/added_{cell}.npz")
        total = len(candidates["a"])
        blocks = (total + 511) // 512
        left = min(total, (blocks * args.rank // args.workers) * 512)
        right = min(total, (blocks * (args.rank + 1) // args.workers) * 512)
        a, b = candidates["a"][left:right], candidates["b"][left:right]
        path = out / f"{cell}.npy"
        progress = out / f"{cell}_PROGRESS.json"
        if path.exists():
            state = read(progress)
            assert (state["left"], state["right"], state["identity"]) == (left, right, identity)
            values = np.lib.format.open_memmap(path, mode="r+")
            done = state["completed"]
            assert values.shape == (len(a), len(SCORERS)) and np.isfinite(values[:done]).all()
        else:
            values = np.lib.format.open_memmap(path, mode="w+", dtype=np.float64, shape=(len(a), len(SCORERS)))
            values[:] = np.nan
            values.flush()
            done = 0
            atomic(progress, {"identity": identity, "left": left, "right": right, "completed": 0, "total": len(a)})
        while done < len(a):
            end = min(done + 512, len(a))
            values[done:end] = scorer.scores(a[done:end], b[done:end])
            values.flush()
            processed += end - done
            done = end
            state = {"identity": identity, "at_utc": now(), "cell": cell, "left": left, "right": right,
                     "completed": done, "total": len(a), "this_run_pairs": processed,
                     "elapsed_seconds": time.monotonic() - started, "pairs_per_second": processed / (time.monotonic() - started)}
            atomic(progress, state)
            if args.stop_after_blocks and processed >= 512 * args.stop_after_blocks:
                print({"qualified_pilot_checkpoint": state}, flush=True)
                return
            if done % 4096 == 0 or done == len(a):
                print(state, flush=True)
            if stop[0]:
                raise SystemExit(75)
        assert np.isfinite(values).all()
        count = min(17, len(a))
        reversal = float(np.max(np.abs(scorer.scores(b[:count], a[:count]) - values[:count]))) if count else 0.
        assert reversal <= tolerance, (args.method, reversal)
        files.append({**record(path, out), "cell": cell, "left": left, "right": right, "scorers": list(SCORERS),
                      "reversal_max_absolute_error": reversal})
    final = [learned_digest(m) for m in scorer.models] if args.method == "dscript_retrained" else learned_digest(scorer.model)
    assert initial == final
    write(out / "COMPLETE.json", {**identity, "at_utc": now(), "files": files, "elapsed_seconds": time.monotonic() - started,
          "training_performed": False, "test_truth_read": False, "learned_parameters_unchanged": True})


if __name__ == "__main__":
    main()
