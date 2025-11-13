from Model.truth_dare_list import TruthDareList


# T-009 — US-012: Add truths and dares and retrieve them
def test_add_truth_and_dare_and_get():
    lst = TruthDareList()

    initial_count = lst.get_count()

    lst.add_truth("Test Truth", "Alice")
    lst.add_dare("Test Dare", "Bob")

    truths = lst.get_truths()
    dares = lst.get_dares()
    counts = lst.get_count()

    assert counts["truths"] == initial_count["truths"] + 1
    assert counts["dares"] == initial_count["dares"] + 1

    assert truths[-1]["text"] == "Test Truth"
    assert dares[-1]["text"] == "Test Dare"


# T-008 — US-008: set_custom_defaults resets and applies defaults
def test_set_custom_defaults():
    lst = TruthDareList()

    custom_truths = ["T1", "T2"]
    custom_dares = ["D1"]

    lst.set_custom_defaults(custom_truths, custom_dares)

    counts = lst.get_count()
    assert counts["truths"] == 2
    assert counts["dares"] == 1

    texts_truths = [t["text"] for t in lst.get_truths()]
    texts_dares = [d["text"] for d in lst.get_dares()]

    assert texts_truths == custom_truths
    assert texts_dares == custom_dares
