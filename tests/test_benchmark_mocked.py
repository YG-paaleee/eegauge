import eegauge.benchmark as benchmark


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

    def colorbar(self, image, ax=None):
        return None


class FakeAxis:
    def bar(self, labels, values, color=None):
        return None

    def axhline(self, y, linestyle=None, color=None, label=None):
        return None

    def legend(self):
        return None

    def imshow(self, matrix, cmap=None):
        return object()

    def set_ylim(self, start, end):
        return None

    def set_xticks(self, ticks):
        return None

    def set_yticks(self, ticks):
        return None

    def set_xticklabels(self, labels, rotation=None, ha=None):
        return None

    def set_yticklabels(self, labels):
        return None

    def set_xlabel(self, label):
        return None

    def set_ylabel(self, label):
        return None

    def set_title(self, title):
        return None

    def text(self, index, value, label, ha=None, va=None):
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


class FakeBinomResult:
    def __init__(self, pvalue):
        self.pvalue = pvalue


def _fake_confusion_matrix(truth, predictions, labels=None):
    pairs = list(zip(truth, predictions, strict=True))
    return [
        [sum(1 for t, p in pairs if t == actual and p == predicted) for predicted in labels]
        for actual in labels
    ]


def _fake_prfs(truth, predictions, labels=None, zero_division=0):
    precision = [1.0 for _ in labels]
    recall = [1.0 for _ in labels]
    f1 = [1.0 for _ in labels]
    support = [sum(1 for t in truth if t == label) for label in labels]
    return precision, recall, f1, support


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
        "confusion_matrix": _fake_confusion_matrix,
        "precision_recall_fscore_support": _fake_prfs,
        "binomtest": lambda k, n, p=0.5, alternative="greater": FakeBinomResult(0.01),
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
    assert result["chance_level"] == 0.5
    assert result["n_test_trials"] == 8
    assert result["significance"]["above_chance"] is True
    assert result["significance"]["p_value"] == 0.01
    assert {item["class"] for item in result["per_class_metrics"]} == {"left", "right"}
    assert result["confusion_matrix"]["labels"] == ["left", "right"]
    assert len(result["confusion_matrix"]["matrix"]) == 2
    assert (tmp_path / "BNCI2014_001.png").exists()
    assert (tmp_path / "BNCI2014_001_confusion.png").exists()
    assert metadata.subjects_used == [1, 2]
    assert metadata.n_channels == 2
    assert metadata.sampling_rate_hz == 250
    assert metadata.channel_type_counts == {"eeg": 2, "eog": 1, "stim": 1}
