from eval.metrics import recall_at_k, top1


def test_top1_true() -> None:
    assert top1([5, 2, 9], 5) is True


def test_top1_false() -> None:
    assert top1([2, 5, 9], 5) is False
    assert top1([], 5) is False


def test_recall_at_k() -> None:
    assert recall_at_k([1, 2, 5, 8], 5, k=5) is True
    assert recall_at_k([1, 2, 3, 4, 9], 5, k=5) is False
    assert recall_at_k([5], 5, k=5) is True


def test_recall_at_k_k_larger_than_list() -> None:
    assert recall_at_k([5], 5, k=100) is True
    assert recall_at_k([1], 5, k=100) is False
