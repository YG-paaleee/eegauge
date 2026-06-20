from bcicards.datasets import SUPPORTED_DATASETS, _first_raw, load_sample_info


class FakeRaw:
    ch_names = ["C3", "C4", "EOG1", "STI"]
    info = {"sfreq": 250.0, "nchan": 4}

    def get_channel_types(self):
        return ["eeg", "eeg", "eog", "stim"]


class FakeDataset:
    def get_data(self, subjects):
        assert subjects == [1]
        return {1: {"0train": {"0": FakeRaw()}}}


def test_load_sample_info_extracts_eeg_channels_and_sampling_rate():
    info = load_sample_info(FakeDataset(), 1)

    assert info["channels"] == ["C3", "C4"]
    assert info["channel_type_counts"] == {"eeg": 2, "eog": 1, "stim": 1}
    assert info["raw_channel_count"] == 4
    assert info["sampling_rate_hz"] == 250.0


def test_supported_datasets_include_additional_motor_imagery_sets():
    for name in ("BNCI2014_001", "BNCI2014_004", "Zhou2016", "Weibo2014"):
        assert name in SUPPORTED_DATASETS
        # Registry maps the public name to a MOABB class name.
        assert SUPPORTED_DATASETS[name]


def test_first_raw_rejects_empty_subject_data():
    try:
        _first_raw({})
    except ValueError as exc:
        assert "no raw runs" in str(exc)
    else:
        raise AssertionError("Expected empty subject data to fail.")
