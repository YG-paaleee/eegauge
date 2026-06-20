import bcicards.benchmark as benchmark


class FakeArray:
    def __init__(self, rows, shape):
        self._rows = list(rows)
        self.shape = shape
        self.ndim = len(shape)

    def __len__(self):
        return len(self._rows)

    def __getitem__(self, index):
        if isinstance(index, list):
            return FakeArray([self._rows[i] for i in index], (len(index), *self.shape[1:]))
        return self._rows[index]


class FakeSeries:
    def __init__(self, values):
        self._values = values

    def tolist(self):
        return list(self._values)


class FakeFrame:
    columns = ["subject"]

    def __init__(self, subjects):
        self._subjects = subjects

    def __getitem__(self, key):
        assert key == "subject"
        return FakeSeries(self._subjects)


class FakeLabels(list):
    def __getitem__(self, index):
        if isinstance(index, list):
            return FakeLabels([super(FakeLabels, self).__getitem__(i) for i in index])
        return super().__getitem__(index)

    def tolist(self):
        return list(self)


class FakeNumpy:
    @staticmethod
    def asarray(values):
        return FakeLabels(values)


class FakePipeline:
    def fit(self, x_train, y_train):
        self._majority = max(set(y_train), key=list(y_train).count)
        return self

    def predict(self, x_test):
        return FakeLabels([self._majority for _ in range(len(x_test))])


class FakeLeaveOneGroupOut:
    def split(self, x_data, labels, groups):
        groups = list(groups)
        for group in sorted(set(groups)):
            test = [index for index, value in enumerate(groups) if value == group]
            train = [index for index, value in enumerate(groups) if value != group]
            yield train, test


class FakePlot:
    def subplots(self, figsize=None):
        return FakeFigure(), FakeAxis()

    def close(self, figure):
        return None


class FakeFigure:
    def tight_layout(self):
        return None

    def savefig(self, target, dpi=None):
        target.write_bytes(b"fake-png")


class FakeAxis:
    def bar(self, labels, values, color=None):
        return None

    def set_ylim(self, start, end):
        return None

    def set_ylabel(self, label):
        return None

    def set_title(self, title):
        return None

    def text(self, index, value, label, ha=None):
        return None


class FakeDataset:
    code = "BNCI2014-001"
    event_id = {"left_hand": 1, "right_hand": 2}
    subject_list = [1, 2]
    sessions_per_subject = 2
    interval = [0, 4]
    sampling_rate = 250


class FakeMotorImagery:
    def get_data(self, dataset, subjects):
        x_data = FakeArray(range(8), (8, 2, 10))
        labels = FakeLabels(["left", "right", "left", "right", "left", "right", "left", "right"])
        frame = FakeFrame([1, 1, 1, 1, 2, 2, 2, 2])
        return x_data, labels, frame


def fake_stack():
    return {
        "plt": FakePlot(),
        "np": FakeNumpy(),
        "CSP": lambda **kwargs: object(),
        "MotorImagery": FakeMotorImagery,
        "LinearDiscriminantAnalysis": lambda: object(),
        "accuracy_score": lambda truth, predictions: (
            sum(t == p for t, p in zip(truth, predictions, strict=True)) / len(truth)
        ),
        "balanced_accuracy_score": lambda truth, predictions: 0.5,
        "LeaveOneGroupOut": FakeLeaveOneGroupOut,
        "StratifiedShuffleSplit": lambda **kwargs: None,
        "make_pipeline": lambda *steps: FakePipeline(),
    }


def test_run_benchmark_uses_subject_aware_split_and_writes_plot(monkeypatch, tmp_path):
    monkeypatch.setattr(benchmark, "_import_scientific_stack", fake_stack)
    monkeypatch.setattr(benchmark, "get_dataset", lambda name: FakeDataset())
    monkeypatch.setattr(
        benchmark,
        "load_sample_info",
        lambda dataset, subject: {
            "channels": ["C3", "C4"],
            "channel_type_counts": {"eeg": 2, "eog": 1, "stim": 1},
            "raw_channel_count": 4,
            "sampling_rate_hz": 250,
        },
    )

    result, metadata = benchmark.run_benchmark(
        "BNCI2014_001",
        [1, 2],
        plot_dir=tmp_path,
    )

    assert result["dataset"] == "BNCI2014_001"
    assert result["paradigm"] == "motor imagery"
    assert result["pipeline"] == "CSP + LDA"
    assert result["split_method"] == "leave-one-subject-out"
    assert set(result["metrics"]) == {"accuracy", "balanced_accuracy"}
    assert result["seed"] == 42
    assert result["library_versions"]
    assert (tmp_path / "BNCI2014_001.png").exists()
    assert metadata.subjects_used == [1, 2]
    assert metadata.n_channels == 2
    assert metadata.sampling_rate_hz == 250
    assert metadata.channel_type_counts == {"eeg": 2, "eog": 1, "stim": 1}
