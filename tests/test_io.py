import json

from bcicards.io import safe_name, write_json


def test_safe_name_keeps_dataset_id_readable():
    assert safe_name("BNCI2014_001") == "BNCI2014_001"
    assert safe_name("bad/name with spaces") == "bad-name-with-spaces"


def test_write_json_serializes_sorted_pretty_payload(tmp_path):
    target = tmp_path / "results" / "sample.json"

    write_json(target, {"b": 2, "a": 1})

    assert json.loads(target.read_text(encoding="utf-8")) == {"a": 1, "b": 2}
    assert target.read_text(encoding="utf-8").startswith("{\n  \"a\"")

