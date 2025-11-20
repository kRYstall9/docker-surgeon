from app.backend.utils.string_utils import normalize_escapes

def test_normalize_newline():
    assert normalize_escapes("line\\nend") == "line\nend"

def test_normalize_unicode():
    assert normalize_escapes("\\u00E9") == "é"

def test_non_string_returns_same():
    assert normalize_escapes(123) == 123


def test_normalize_escapes_exception():
    # create a str subclass that raises on encode to trigger the exception branch
    class BrokenStr(str):
        def encode(self, *args, **kwargs):
            raise Exception('bad encode')

    s = BrokenStr('abc')
    assert normalize_escapes(s) == s