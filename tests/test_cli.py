import pytest

from bcicards.cli import build_parser


def test_top_level_help_smoke():
    parser = build_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--help"])

    assert exc.value.code == 0


def test_benchmark_requires_subjects():
    parser = build_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["benchmark", "--dataset", "BNCI2014_001"])

    assert exc.value.code == 2

