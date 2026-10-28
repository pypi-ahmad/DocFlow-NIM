import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PIL import Image

from docflow import conversion
from docflow.image_limits import check_image_size
from docflow.space_ui import cleanup, prepare


class DocumentLimitTests(unittest.TestCase):
    def setUp(self):
        self.renders = []
        pdf = MagicMock()
        pdf.__enter__.return_value = pdf
        pdf.__len__.return_value = 8

        def page(index):
            item = MagicMock()
            item.get_width.return_value = item.get_height.return_value = 20
            def render(**kwargs):
                self.renders.append(index + 1)
                bitmap = MagicMock()
                bitmap.to_pil.return_value = Image.new("RGB", (20, 20))
                return bitmap
            item.render.side_effect = render
            return item

        pdf.__getitem__.side_effect = page
        self.pdf_patch = patch.object(conversion.pdfium, "PdfDocument", return_value=pdf)
        self.pdf_patch.start()
        self.addCleanup(self.pdf_patch.stop)

    def test_preflight_counts_without_rendering(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sample.pdf"
            path.write_bytes(b"dummy fixture")
            state = prepare([str(path)], 8, 8, {})
            try:
                self.assertEqual(self.renders, [])
                self.assertEqual(state["jobs"][0]["first"], 8)
            finally:
                cleanup(state)
            with self.assertRaisesRegex(ValueError, "five pages"):
                prepare([str(path)], 1, 0, {})
            self.assertEqual(self.renders, [])

    def test_pdf_renders_only_selected_page(self):
        pages = list(conversion.page_images(b"fixture", "sample.pdf", 8, 8))
        try:
            self.assertEqual(self.renders, [8])
            self.assertEqual(len(pages), 1)
        finally:
            for image in pages:
                image.close()

    def test_conversion_preserves_original_page_number(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "postprocessing.py").touch()
            postprocessor = SimpleNamespace(postprocess_document=lambda *args, **kwargs:
                                           {"markdown": "sample", "blocks": []})
            raw = SimpleNamespace(content="sample", finish_reason="stop", usage={}, complete=True)
            with (patch.object(conversion, "MODEL", root),
                  patch.object(conversion.importlib, "import_module", return_value=postprocessor)):
                result, output = conversion.convert(b"fixture", "sample.pdf", "space-gpu", 8, 8,
                                                    page_parser=lambda image: raw, output_root=root)
            self.assertEqual(self.renders, [8])
            self.assertEqual([page["number"] for page in result["pages"]], [8])
            self.assertTrue((output / "page-8.png").is_file())
            self.assertFalse((output / "page-1.png").exists())

    def test_large_image_rejected_before_rgb(self):
        image = MagicMock()
        image.__enter__.return_value = image
        image.size, image.n_frames = (40_000_001, 1), 1
        with (
            patch.object(conversion.Image, "open", return_value=image),
            self.assertRaisesRegex(ValueError, "40 megapixels"),
        ):
            list(conversion.page_images(b"fixture", "sample.png"))
        image.convert.assert_not_called()

    def test_selected_tiff_frame(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sample.tiff"
            red, blue = Image.new("RGB", (20, 20), "red"), Image.new("RGB", (20, 20), "blue")
            red.save(path, save_all=True, append_images=[blue])
            self.assertEqual(conversion.page_count(path.read_bytes(), path.name), 2)
            pages = list(conversion.page_images(path.read_bytes(), path.name, 2, 2))
            try:
                self.assertEqual(len(pages), 1)
                self.assertEqual(pages[0].getpixel((0, 0)), (0, 0, 255))
            finally:
                red.close()
                blue.close()
                for image in pages:
                    image.close()

    def test_pixel_boundary(self):
        check_image_size((8000, 5000))
        for size in [(8001, 5000), (0, 1), (-1, 1)]:
            with self.assertRaises(ValueError):
                check_image_size(size)


if __name__ == "__main__":
    unittest.main()
