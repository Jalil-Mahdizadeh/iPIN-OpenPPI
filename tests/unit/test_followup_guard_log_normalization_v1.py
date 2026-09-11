import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("guard_normalization_fixture", Path(__file__).resolve().parents[2] / "scripts/benchmark/normalize_followup_guard_log_v1.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class GuardLogFixtures(unittest.TestCase):
    def test_known_prefix_removed_without_altering_attestation(self):
        value = {k: True for k in ("child_inherits_filter", "cpu_only", "network_syscall_filter_enforced", "no_inherited_descriptors_above_stderr", "proc_sys_hidden")}
        encoded = json.dumps(value).encode() + b"\n"
        actual, n = module.parse(b"[1789129113.560836] [synthetic:1:0]             sys.c:306  UCX  ERROR failed to get boot id\n" + encoded)
        self.assertEqual(actual, encoded)
        self.assertEqual(n, 1)

    def test_unknown_output_or_failed_guard_is_not_hidden(self):
        for payload in (b"unrecognized error\n{}\n", b"{}\n", b"{}\n{}\n"):
            with self.assertRaises(RuntimeError):
                module.parse(payload)
