"""Offline regression checks: python3 .github/actions/verify-container-attestations/test_verification.py."""

import json
import os
from pathlib import Path
import re
import subprocess
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[3]
ACTION = Path(__file__).with_name("action.yml").read_text()
SCRIPTS = [
    textwrap.dedent(block)
    for block in re.findall(r"^      run: \|\n((?:^        .*\n|^\n)+)", ACTION, re.M)
    if "VERIFICATION_PASSED" in block
]
MOCK_GH = """
gh() {
  printf 'GH_CALL\\n'
  printf 'ARG:%s\\n' "$@"
  [[ "$3" != "${MOCK_FAIL_CONTAINER:-}" ]]
}
"""


class VerificationTests(unittest.TestCase):
    def run_step(self, script, containers, repository="octobooth/security-octo-supply", failure=""):
        env = {
            **os.environ,
            "CONTAINERS": json.dumps(containers),
            "ATTESTATION_REPOSITORY": repository,
            "GH_HOSTNAME": "github.com",
            "VERIFICATION_TYPE": "attestation",
            "GITHUB_OUTPUT": "/dev/stdout",
            "MOCK_FAIL_CONTAINER": failure,
        }
        return subprocess.run(
            ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", MOCK_GH + script],
            env=env, text=True, capture_output=True, check=False,
        )

    def test_local_signer_for_organization_and_personal_copies(self):
        self.assertEqual(len(SCRIPTS), 2)
        for repository in ("octobooth/security-octo-supply", "octobooth/security-octo-supply-v4", "personal/demo"):
            for index, script in enumerate(SCRIPTS):
                with self.subTest(repository=repository, step=index):
                    result = self.run_step(script, ["ghcr.io/example/api:main-test"], repository)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("VERIFICATION_PASSED=true", result.stdout)
                    self.assertIn(f"ARG:--repo\nARG:{repository}\n", result.stdout)
                    self.assertIn(
                        f"ARG:--signer-workflow\nARG:{repository}/.github/workflows/build-publish-containers.yml\n",
                        result.stdout,
                    )
                    if index == 1:
                        self.assertIn("ARG:--predicate-type\nARG:https://spdx.dev/Document/v2.3\n", result.stdout)

    def test_failure_is_not_lost_when_a_later_container_passes(self):
        for script in SCRIPTS:
            result = self.run_step(script, ["bad-image", "good-image"], failure="oci://bad-image")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.count("GH_CALL"), 2)
            self.assertIn("VERIFICATION_PASSED=false", result.stdout)
            self.assertNotIn("VERIFICATION_PASSED=true", result.stdout)

    def test_empty_or_invalid_containers_do_not_report_success(self):
        for script in SCRIPTS:
            for containers in ([], {}, [""], [1], "not an array"):
                with self.subTest(containers=containers):
                    result = self.run_step(script, containers)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertNotIn("GH_CALL", result.stdout)
                    self.assertNotIn("VERIFICATION_PASSED=true", result.stdout)

    def test_container_is_passed_as_data_not_shell_code(self):
        for script in SCRIPTS:
            result = self.run_step(script, ['image:tag; printf INJECTION_EXECUTED >&2'])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("INJECTION_EXECUTED", result.stderr)
            self.assertIn("ARG:oci://image:tag; printf INJECTION_EXECUTED >&2", result.stdout)

    def test_demo_script_checks_local_signer_and_propagates_failure(self):
        script = (ROOT / "demo/resources/verify-attestation.sh").read_text()
        function = script.split("verify_attestation() {", 1)[1].split("# Main execution", 1)[0]
        function = "verify_attestation() {" + function
        setup = "log_info() { :; }; log_error() { :; }; GREEN=; RED=; NC=;\n"
        for failure in ("", "oci://ghcr.io/personal/demo-api:main-test"):
            result = self.run_step(
                setup + function + '\nverify_attestation personal/demo main-test github.com\n',
                [], failure=failure,
            )
            self.assertEqual(result.returncode, 1 if failure else 0, result.stderr)
            self.assertIn("ARG:--signer-repo\nARG:personal/demo\n", result.stdout)
            self.assertIn(
                "ARG:--signer-workflow\nARG:personal/demo/.github/workflows/build-publish-containers.yml\n",
                result.stdout,
            )


if __name__ == "__main__":
    unittest.main()
