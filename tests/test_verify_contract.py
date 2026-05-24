#!/usr/bin/env python3
"""tests/test_verify_contract.py — regression tests for verify_contract.py
parser + validator-block extraction. Pure stdlib unittest.
"""
import importlib.util, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Dynamically import the helper (so we don't need to install as a package)
spec = importlib.util.spec_from_file_location("verify_contract", REPO / "tools" / "verify_contract.py")
vc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vc)


CONTRACT_OK = """\
goal: |
  test goal that is long enough to pass min char check 30 chars
scope: |
  test scope that is long enough to pass min char check 30 chars
metric: |
  primary metric SR >= 0.7 at step 5M (must be 30 char+)
verify: |
  3 seeds; baseline run_0 locked; bootstrap CI
guard: |
  if SR < 0.4 then PIVOT (trigger)
"""

CONTRACT_WITH_VALIDATORS = CONTRACT_OK + """\
validators:
  - type: arxiv
    id: 2410.24164    # inline comment should be stripped
  - type: partition
    name: gpu
    host: hpcc
  - type: hf_repo
    id: foo/bar
    kind: model
"""

CONTRACT_BAD_THRESHOLD = """\
goal: |
  goal long enough to pass min char check 30 chars yes
scope: |
  scope long enough to pass min char check 30 chars yes
metric: |
  metric long enough to pass min char check 30 chars yes
verify: |
  verify long enough to pass min char check 30 chars yes + seed
guard: |
  guard sentence with no numeric threshold whatsoever here
"""


class TestParseYaml(unittest.TestCase):
    def test_basic_pipe_multiline(self):
        out = vc.parse_yaml(CONTRACT_OK)
        for f in ["goal", "scope", "metric", "verify", "guard"]:
            self.assertIn(f, out)
            self.assertGreaterEqual(len(out[f]), 30)

    def test_validators_extracted(self):
        out = vc.parse_yaml(CONTRACT_WITH_VALIDATORS)
        vs = out["__validators__"]
        self.assertEqual(len(vs), 3)
        self.assertEqual(vs[0]["type"], "arxiv")
        # inline comment must be stripped (was a real bug we caught in live test)
        self.assertEqual(vs[0]["id"], "2410.24164")
        self.assertEqual(vs[1]["type"], "partition")
        self.assertEqual(vs[1]["name"], "gpu")
        self.assertEqual(vs[1]["host"], "hpcc")
        self.assertEqual(vs[2]["type"], "hf_repo")
        self.assertEqual(vs[2]["id"], "foo/bar")

    def test_inline_comment_stripping(self):
        text = "key: value  # comment with trailing spaces\n"
        self.assertEqual(vc._strip_inline_comment("value  # comment"), "value")
        self.assertEqual(vc._strip_inline_comment("value"), "value")
        self.assertEqual(vc._strip_inline_comment("value  # cmt with #hash"), "value")


class TestRunVerify(unittest.TestCase):
    def _run_on(self, text):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write(text); p = Path(f.name)
        try:
            return vc.run_verify(p)
        finally:
            p.unlink()

    def test_valid_contract(self):
        self.assertEqual(self._run_on(CONTRACT_OK), 0)

    def test_no_threshold_fails(self):
        self.assertEqual(self._run_on(CONTRACT_BAD_THRESHOLD), 1)


class TestValidatorsBlockSeparate(unittest.TestCase):
    """Verify the validators block detection doesn't eat into following keys."""

    def test_validators_block_followed_by_field(self):
        text = CONTRACT_WITH_VALIDATORS + "\nnotes: trailing field after validators\n"
        out = vc.parse_yaml(text)
        # validators captured
        self.assertEqual(len(out["__validators__"]), 3)
        # AND the trailing scalar is also captured
        self.assertEqual(out.get("notes"), "trailing field after validators")


if __name__ == "__main__":
    unittest.main(verbosity=2)
