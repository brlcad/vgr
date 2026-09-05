import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("vgr_metrics", ROOT / "tools" / "vgr_metrics.py")
VGR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VGR)


class MetricsTest(unittest.TestCase):
    def setUp(self):
        self.reference = json.loads((ROOT / "config" / "vgr-reference.json").read_text())

    def test_reference_logs_are_exactly_one_vgr(self):
        observations = {
            name: dict(values) for name, values in self.reference["scenes"].items()
        }
        observations["sphflake"] = {
            "pixels": 262144,
            "rays": 1000,
            "seconds": 10.0,
            "rtfm": 100.0,
        }
        result = VGR.calculate(self.reference, observations, 1_000_000)
        self.assertAlmostEqual(result["legacy_vgr_arithmetic_mean"], 1.0)
        self.assertAlmostEqual(result["sphflake"]["projected_vax_reference_rtfm"], 100.0)
        self.assertAlmostEqual(result["suggested_throttle_cycles_per_second"], 1_000_000)

    def test_linear_normalization(self):
        observations = {}
        for name, values in self.reference["scenes"].items():
            observations[name] = {**values, "rtfm": values["rtfm"] * 4.0}
        observations["sphflake"] = {
            "pixels": 262144,
            "rays": 8000,
            "seconds": 10.0,
            "rtfm": 800.0,
        }
        result = VGR.calculate(self.reference, observations, 2_000_000)
        self.assertAlmostEqual(result["legacy_vgr_arithmetic_mean"], 4.0)
        self.assertAlmostEqual(result["sphflake"]["projected_vax_reference_rtfm"], 200.0)
        self.assertAlmostEqual(result["suggested_throttle_cycles_per_second"], 500_000)

    def test_parser_uses_canonical_rtfm_line(self):
        text = (
            "root@vax780.local:/usr/src/rt\n"
            "Frame 0: 262144 pixels in 88.18 sec = 2972.83 pixels/sec\n"
            "Frame 0: 1307010 rays in 88.18 sec = 14821.48 rays/sec (RTFM)\n"
        )
        parsed = VGR.parse_rtfm(text, "test")
        self.assertEqual(parsed["pixels"], 262144)
        self.assertEqual(parsed["rtfm"], 14821.48)
        self.assertEqual(parsed["host"], "vax780.local")

    def test_rejects_reduced_resolution(self):
        observations = {
            name: {**values, "pixels": 4096}
            for name, values in self.reference["scenes"].items()
        }
        with self.assertRaisesRegex(ValueError, "not a 512x512 benchmark"):
            VGR.calculate(self.reference, observations, 1_000_000)


if __name__ == "__main__":
    unittest.main()
