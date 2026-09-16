from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


class CpeSsotTests(unittest.TestCase):
    def test_cpe_records_both_physical_hosts(self):
        text = (REPO / "docs/CIVICVS_PROJECT_ENVIRONMENT.md").read_text()
        for token in (
            "10.110.0.4",
            "10.110.0.9",
            "CPE Build and Hardware Workstation",
            "Dell Precision",
            "Ubuntu LXD",
            "/home/cpe-build",
            "/home/civicus-build",
        ):
            self.assertIn(token, text)

    def test_fixed_usb_roles_are_recorded(self):
        text = (REPO / "docs/CIVICVS_PROJECT_ENVIRONMENT.md").read_text()
        self.assertIn("CPE-USB-1  front port 1  USB branch 1.1.2  PROGRAM", text)
        self.assertIn("CPE-USB-2  front port 2  USB branch 1.1.3  TERMINAL", text)
        self.assertIn("303a:1001", text)
        self.assertIn("10c4:ea60", text)

    def test_current_state_matches_cpe(self):
        state = json.loads((REPO / "docs/CURRENT_STATE.json").read_text())
        self.assertEqual("fw", state["cpe"]["build_hardware_workstation"]["hostname"])
        self.assertEqual(
            "10.110.0.4/22",
            state["cpe"]["build_hardware_workstation"]["cpe_address"],
        )
        self.assertEqual(
            "10.110.0.9/22",
            state["cpe"]["firmware_authority_host"]["cpe_address"],
        )
        self.assertIsNone(
            state["cpe"]["firmware_authority_host"]["firmware_authority_container"]["network_identity"]
        )

    def test_session_start_requires_cpe_for_physical_work(self):
        text = (REPO / "docs/SESSION_START.md").read_text()
        self.assertIn("docs/CIVICVS_PROJECT_ENVIRONMENT.md", text)
        self.assertIn("10.110.0.4", text)
        self.assertIn("10.110.0.9", text)
        self.assertIn("do not use `pct` on the dell", text.lower())

    def test_firmware_authority_distinguishes_host_and_container_identity(self):
        text = (REPO / "ms5/firmware_authority/README.md").read_text()
        self.assertIn("10.110.0.9", text)
        self.assertIn("physical Dell host", text)
        self.assertIn("container network identity", text)
        self.assertIn("read-only LXD", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
