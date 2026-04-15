import csv
import json
import os
import stat
from pathlib import Path
import pytest
from amap_collector.cli.output import flatten_dict, ensure_writable, write_output, OutputError


SAMPLE = [
    {
        "name": "AMAP Test",
        "status": "available_places",
        "website": "http://test.fr",
        "contact": {"name": "Jean", "emails": ["jean@test.fr"], "phones": []},
        "place": {"name": "Salle", "address": "1 rue Test, 75001 PARIS", "delivery_time": "Lundi 18h"},
        "comment": "légumes",
    }
]


class TestFlattenDict:
    def test_flat_entry(self) -> None:
        result = flatten_dict({"a": "x", "b": "y"})
        assert result == {"a": "x", "b": "y"}

    def test_nested_dict_uses_prefix(self) -> None:
        result = flatten_dict({"contact": {"name": "Jean", "emails": ["a@b.fr"]}})
        assert result["contact_name"] == "Jean"
        assert result["contact_emails"] == "a@b.fr"

    def test_list_joined_with_comma(self) -> None:
        result = flatten_dict({"emails": ["a@b.fr", "c@d.fr"]})
        assert result["emails"] == "a@b.fr, c@d.fr"

    def test_empty_list(self) -> None:
        result = flatten_dict({"phones": []})
        assert result["phones"] == ""

    def test_none_becomes_empty_string(self) -> None:
        result = flatten_dict({"website": None})
        assert result["website"] == ""

    def test_deeply_nested(self) -> None:
        result = flatten_dict({"a": {"b": {"c": "deep"}}})
        assert result["a_b_c"] == "deep"

    def test_full_sample_has_expected_keys(self) -> None:
        result = flatten_dict(SAMPLE[0])
        assert set(result.keys()) == {
            "name", "status", "website", "comment",
            "contact_name", "contact_emails", "contact_phones",
            "place_name", "place_address", "place_delivery_time",
        }


class TestEnsureWritable:
    def test_valid_path_returns_resolved(self, tmp_path: Path) -> None:
        out = tmp_path / "out.json"
        resolved = ensure_writable(out)
        assert resolved == out.resolve()

    def test_relative_path_resolved_to_absolute(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        resolved = ensure_writable(Path("out.json"))
        assert resolved.is_absolute()

    def test_nonexistent_directory_raises(self) -> None:
        with pytest.raises(OutputError, match="Directory does not exist"):
            ensure_writable(Path("/nonexistent/dir/out.json"))

    @pytest.mark.skipif(os.getuid() == 0, reason="root bypasses file permission checks")
    def test_readonly_file_raises(self, tmp_path: Path) -> None:
        out = tmp_path / "out.json"
        out.write_text("{}")
        out.chmod(stat.S_IREAD)
        try:
            with pytest.raises(OutputError, match="not writable"):
                ensure_writable(out)
        finally:
            out.chmod(stat.S_IREAD | stat.S_IWRITE)


class TestWriteOutput:
    def test_stdout_when_no_file(self, capsys: pytest.CaptureFixture) -> None:
        write_output(SAMPLE, None)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed[0]["name"] == "AMAP Test"

    def test_json_file_written(self, tmp_path: Path) -> None:
        out = tmp_path / "result.json"
        write_output(SAMPLE, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data[0]["name"] == "AMAP Test"

    def test_csv_file_written(self, tmp_path: Path) -> None:
        out = tmp_path / "result.csv"
        write_output(SAMPLE, out)
        rows = list(csv.DictReader(out.open(encoding="utf-8")))
        assert rows[0]["name"] == "AMAP Test"
        assert rows[0]["contact_name"] == "Jean"

    def test_empty_results_writes_empty_csv(self, tmp_path: Path) -> None:
        out = tmp_path / "result.csv"
        write_output([], out)
        assert out.read_text() == ""

    def test_invalid_directory_raises(self) -> None:
        with pytest.raises(OutputError):
            write_output(SAMPLE, Path("/nonexistent/out.json"))
