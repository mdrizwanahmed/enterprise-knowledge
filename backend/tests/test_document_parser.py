from app.document_parser import extract_pages

def test_extract_text_file(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("RAG retrieves evidence.", encoding="utf-8")
    assert extract_pages(path) == [{"page": None, "text": "RAG retrieves evidence."}]
