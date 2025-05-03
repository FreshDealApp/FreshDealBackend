# tests/test_firebase.py
import os
import io
import unittest
from werkzeug.datastructures import FileStorage
import firebase_admin

# force the code to take the local-fallback path:
firebase_admin._apps.clear()

from src.utils.cloud_storage import upload_file, UPLOAD_FOLDER

class BytesFile(io.BytesIO):
    """A BytesIO that carries a `.filename` attribute."""
    def __init__(self, data: bytes, filename: str):
        super().__init__(data)
        self.filename = filename

class TestCloudStorage(unittest.TestCase):

    def setUp(self):
        # ensure upload folder is clean
        if os.path.isdir(UPLOAD_FOLDER):
            for f in os.listdir(UPLOAD_FOLDER):
                os.remove(os.path.join(UPLOAD_FOLDER, f))

    def fake_url_for(self, endpoint, filename, _external):
        return f"https://test.local/{filename}"

    def test_upload_file_local_fallback(self):
        # load a small fixture
        path = os.path.join(os.path.dirname(__file__), "fixtures", "test.jpg")
        with open(path, "rb") as f:
            data = f.read()

        # wrap it
        bf = BytesFile(data, filename="test.jpg")

        success, url = upload_file(
            bf,
            folder="uploads",
            url_for_func=self.fake_url_for,
            url_endpoint="uploads"
        )

        self.assertTrue(success, "Expected upload_file to succeed in local-fallback")
        self.assertTrue(url.startswith("https://test.local/"))

        # check that the file actually exists on disk
        fname = url.rsplit("/", 1)[-1]
        self.assertTrue(os.path.exists(os.path.join(UPLOAD_FOLDER, fname)))

if __name__ == "__main__":
    unittest.main()
