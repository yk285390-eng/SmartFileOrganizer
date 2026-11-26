"""Tests use temporary folders and never touch personal files."""
import tempfile
import unittest
from pathlib import Path
from organizer import OrganizerError, organize, plan_organization, undo_last

class OrganizerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.source, self.destination = root / "source", root / "destination"
        self.source.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_preview_does_not_move_and_categorizes(self):
        sample = self.source / "photo.JPG"
        sample.write_text("photo")
        result = organize(self.source, self.destination)
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["plan"][0]["category"], "Images")
        self.assertTrue(sample.exists())
        self.assertFalse(self.destination.exists())

    def test_move_avoids_overwrite_and_undo_restores_with_safe_name(self):
        (self.source / "notes.txt").write_text("new")
        target = self.destination / "Documents"
        target.mkdir(parents=True)
        (target / "notes.txt").write_text("existing")
        result = organize(self.source, self.destination, dry_run=False)
        self.assertEqual(len(result["moved"]), 1)
        moved = Path(result["moved"][0]["destination"])
        self.assertEqual(moved.name, "notes (1).txt")
        self.assertEqual((target / "notes.txt").read_text(), "existing")
        undo = undo_last(self.destination)
        self.assertEqual(len(undo["restored"]), 1)
        self.assertEqual((self.source / "notes.txt").read_text(), "new")

    def test_nested_folders_rejected(self):
        with self.assertRaises(OrganizerError):
            plan_organization(self.source, self.source / "inside")

if __name__ == "__main__":
    unittest.main()
