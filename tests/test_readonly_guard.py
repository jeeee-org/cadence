import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "skills" / "cadence" / "hooks" / "readonly-guard.py"


def run_hook(payload):
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


class ReadonlyGuardTest(unittest.TestCase):
    def make_repo(self, base):
        repo = Path(base) / "repo"
        (repo / ".git").mkdir(parents=True)
        return repo

    def test_no_sentinel_allows(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            output = run_hook({"cwd": str(repo), "tool_input": {"file_path": "README.md"}})
            self.assertEqual(output, "")

    def test_claude_write_outside_is_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            (repo / ".cadence").mkdir()
            (repo / ".cadence" / "readonly").touch()
            output = run_hook({"cwd": str(repo), "tool_input": {"file_path": "README.md"}})
            self.assertEqual(json.loads(output)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_claude_run_artifact_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            (repo / ".cadence").mkdir()
            (repo / ".cadence" / "readonly").touch()
            output = run_hook({
                "cwd": str(repo),
                "tool_input": {"file_path": ".cadence/runs/01/state.md"},
            })
            self.assertEqual(output, "")

    def test_claude_non_run_cadence_file_is_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            (repo / ".cadence").mkdir()
            (repo / ".cadence" / "readonly").touch()
            output = run_hook({
                "cwd": str(repo),
                "tool_input": {"file_path": ".cadence/notes.md"},
            })
            self.assertIn("deny", output)

    def test_path_traversal_is_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            (repo / ".cadence").mkdir()
            (repo / ".cadence" / "readonly").touch()
            output = run_hook({
                "cwd": str(repo),
                "tool_input": {"file_path": ".cadence/../README.md"},
            })
            self.assertIn("deny", output)

    def test_symlinked_runs_directory_is_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            outside = repo / "outside"
            outside.mkdir()
            (repo / ".cadence").mkdir()
            (repo / ".cadence" / "readonly").touch()
            (repo / ".cadence" / "runs").symlink_to(outside, target_is_directory=True)
            output = run_hook({
                "cwd": str(repo),
                "tool_input": {"file_path": ".cadence/runs/01/state.md"},
            })
            self.assertIn("deny", output)

    def test_codex_patch_run_artifacts_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            (repo / ".cadence").mkdir()
            (repo / ".cadence" / "readonly").touch()
            patch = "*** Begin Patch\n*** Add File: .cadence/runs/01/state.md\n+x\n*** End Patch"
            output = run_hook({
                "cwd": str(repo),
                "tool_name": "apply_patch",
                "tool_input": {"command": patch},
            })
            self.assertEqual(output, "")

    def test_codex_patch_add_sentinel_is_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            (repo / ".cadence").mkdir()
            (repo / ".cadence" / "readonly").touch()
            patch = "*** Begin Patch\n*** Add File: .cadence/readonly\n+x\n*** End Patch"
            output = run_hook({
                "cwd": str(repo),
                "tool_name": "apply_patch",
                "tool_input": {"command": patch},
            })
            self.assertIn("deny", output)

    def test_codex_patch_update_sentinel_is_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            (repo / ".cadence").mkdir()
            (repo / ".cadence" / "readonly").touch()
            patch = "*** Begin Patch\n*** Update File: .cadence/readonly\n@@\n-old\n+new\n*** End Patch"
            output = run_hook({
                "cwd": str(repo),
                "tool_name": "apply_patch",
                "tool_input": {"command": patch},
            })
            self.assertIn("deny", output)

    def test_codex_patch_delete_sentinel_is_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            (repo / ".cadence").mkdir()
            (repo / ".cadence" / "readonly").touch()
            patch = "*** Begin Patch\n*** Delete File: .cadence/readonly\n*** End Patch"
            output = run_hook({
                "cwd": str(repo),
                "tool_name": "apply_patch",
                "tool_input": {"command": patch},
            })
            self.assertIn("deny", output)

    def test_codex_patch_move_sentinel_is_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            (repo / ".cadence").mkdir()
            (repo / ".cadence" / "readonly").touch()
            patch = (
                "*** Begin Patch\n"
                "*** Update File: .cadence/readonly\n"
                "*** Move to: .cadence/runs/01/readonly\n"
                "@@\n-old\n+new\n"
                "*** End Patch"
            )
            output = run_hook({
                "cwd": str(repo),
                "tool_name": "apply_patch",
                "tool_input": {"command": patch},
            })
            self.assertIn("deny", output)

    def test_codex_patch_outside_is_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            (repo / ".cadence").mkdir()
            (repo / ".cadence" / "readonly").touch()
            patch = "*** Begin Patch\n*** Update File: README.md\n@@\n-old\n+new\n*** End Patch"
            output = run_hook({
                "cwd": str(repo),
                "tool_name": "apply_patch",
                "tool_input": {"command": patch},
            })
            self.assertIn("deny", output)

    def test_codex_mixed_patch_is_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            (repo / ".cadence").mkdir()
            (repo / ".cadence" / "readonly").touch()
            patch = (
                "*** Begin Patch\n"
                "*** Add File: .cadence/runs/01/state.md\n+x\n"
                "*** Update File: README.md\n@@\n-old\n+new\n"
                "*** End Patch"
            )
            output = run_hook({
                "cwd": str(repo),
                "tool_name": "apply_patch",
                "tool_input": {"command": patch},
            })
            self.assertIn("deny", output)

    def test_codex_move_outside_run_artifacts_is_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            (repo / ".cadence").mkdir()
            (repo / ".cadence" / "readonly").touch()
            patch = (
                "*** Begin Patch\n"
                "*** Update File: .cadence/runs/01/state.md\n"
                "*** Move to: README.md\n@@\n-old\n+new\n"
                "*** End Patch"
            )
            output = run_hook({
                "cwd": str(repo),
                "tool_name": "apply_patch",
                "tool_input": {"command": patch},
            })
            self.assertIn("deny", output)

    def test_unparseable_patch_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            (repo / ".cadence").mkdir()
            (repo / ".cadence" / "readonly").touch()
            output = run_hook({
                "cwd": str(repo),
                "tool_name": "apply_patch",
                "tool_input": {"command": "not a patch"},
            })
            self.assertIn("deny", output)

    def test_nested_cwd_finds_repo_sentinel(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            nested = repo / "src" / "pkg"
            nested.mkdir(parents=True)
            (repo / ".cadence").mkdir()
            (repo / ".cadence" / "readonly").touch()
            output = run_hook({
                "cwd": str(nested),
                "tool_input": {"file_path": str(repo / "README.md")},
            })
            self.assertIn("deny", output)

    def test_nested_cwd_relative_cadence_path_is_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            nested = repo / "src"
            nested.mkdir()
            (repo / ".cadence").mkdir()
            (repo / ".cadence" / "readonly").touch()
            patch = "*** Begin Patch\n*** Add File: .cadence/runs/01/state.md\n+x\n*** End Patch"
            output = run_hook({
                "cwd": str(nested),
                "tool_name": "apply_patch",
                "tool_input": {"command": patch},
            })
            self.assertIn("deny", output)

    def test_nested_cwd_relative_root_run_artifact_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            nested = repo / "src"
            nested.mkdir()
            (repo / ".cadence" / "runs" / "01").mkdir(parents=True)
            (repo / ".cadence" / "readonly").touch()
            patch = "*** Begin Patch\n*** Add File: ../.cadence/runs/01/state.md\n+x\n*** End Patch"
            output = run_hook({
                "cwd": str(nested),
                "tool_name": "apply_patch",
                "tool_input": {"command": patch},
            })
            self.assertEqual(output, "")

    def test_nested_git_does_not_inherit_outer_sentinel(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            nested_repo = repo / "vendor" / "nested"
            nested_cwd = nested_repo / "src"
            (nested_repo / ".git").mkdir(parents=True)
            nested_cwd.mkdir()
            (repo / ".cadence").mkdir()
            (repo / ".cadence" / "readonly").touch()
            output = run_hook({
                "cwd": str(nested_cwd),
                "tool_input": {"file_path": str(nested_repo / "README.md")},
            })
            self.assertEqual(output, "")

    def test_nested_git_uses_its_own_sentinel(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.make_repo(temp)
            nested_repo = repo / "vendor" / "nested"
            nested_cwd = nested_repo / "src"
            (nested_repo / ".git").mkdir(parents=True)
            nested_cwd.mkdir()
            (nested_repo / ".cadence").mkdir()
            (nested_repo / ".cadence" / "readonly").touch()
            output = run_hook({
                "cwd": str(nested_cwd),
                "tool_input": {"file_path": str(nested_repo / "README.md")},
            })
            self.assertIn("deny", output)


if __name__ == "__main__":
    unittest.main()
