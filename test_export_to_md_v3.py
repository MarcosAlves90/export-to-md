import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from export_to_md_v3 import main


class ExportToMarkdownTests(unittest.TestCase):
    def run_cli(self, args: list[str]) -> int:
        with redirect_stdout(StringIO()):
            return main(args)

    def test_exports_into_source_named_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            source = workspace / "sample-project"
            source.mkdir()
            (source / "README.md").write_text("# Sample\n", encoding="utf-8")

            output_base = workspace / "markdown_export"

            exit_code = self.run_cli([str(source), "-o", str(output_base)])

            self.assertEqual(exit_code, 0)
            export_dir = output_base / "sample-project"
            self.assertTrue((export_dir / "TREE.md").exists())
            self.assertTrue((export_dir / "SUMMARY.md").exists())
            self.assertTrue((export_dir / "PROJECT_CONTEXT.md").exists())
            self.assertTrue((export_dir / "README.md.md").exists())

    def test_excludes_gitignore_matches_and_output_base(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            source = workspace / "sample-project"
            source.mkdir()
            (source / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
            (source / "included.txt").write_text("included\n", encoding="utf-8")
            (source / "ignored.txt").write_text("ignored\n", encoding="utf-8")
            output_base = source / "markdown_export"
            previous_export = output_base / "sample-project"
            previous_export.mkdir(parents=True)
            (previous_export / "stale.txt").write_text("stale\n", encoding="utf-8")

            exit_code = self.run_cli([str(source), "-o", str(output_base)])

            self.assertEqual(exit_code, 0)
            export_dir = output_base / "sample-project"
            tree = (export_dir / "TREE.md").read_text(encoding="utf-8")
            self.assertIn("included.txt", tree)
            self.assertNotIn("ignored.txt", tree)
            self.assertNotIn("markdown_export", tree)

    def test_omits_binary_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            source = workspace / "sample-project"
            source.mkdir()
            (source / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00")

            exit_code = self.run_cli([str(source), "-o", str(workspace / "out")])

            self.assertEqual(exit_code, 0)
            output = (workspace / "out" / "sample-project" / "image.png.md").read_text(
                encoding="utf-8",
            )
            self.assertIn("File is probably binary. Raw content omitted.", output)

    def test_omits_files_above_configured_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            source = workspace / "sample-project"
            source.mkdir()
            (source / "large.txt").write_text("x" * 2_000_000, encoding="utf-8")

            exit_code = self.run_cli([
                str(source),
                "-o",
                str(workspace / "out"),
                "--max-file-size-mb",
                "1",
            ])

            self.assertEqual(exit_code, 0)
            output = (workspace / "out" / "sample-project" / "large.txt.md").read_text(
                encoding="utf-8",
            )
            self.assertIn("File omitted because it exceeds the configured limit", output)


if __name__ == "__main__":
    unittest.main()
