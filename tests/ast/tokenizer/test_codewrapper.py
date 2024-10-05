from contextlib import ExitStack
import pytest

from pyaspparsing.ast.tokenizer.codewrapper import CharacterType, CodeWrapper


def test_properties():
    with CodeWrapper("a", False) as cwrap:
        assert cwrap.current_char == "a"
        assert cwrap.current_idx == 0


def test_invalid_enter():
    with ExitStack() as stack:
        stack.enter_context(pytest.raises(RuntimeError))
        cwrap: CodeWrapper = stack.enter_context(CodeWrapper("", False))
        stack.enter_context(cwrap)


def test_premature_check_for_end():
    cwrap = CodeWrapper("")
    with pytest.raises(RuntimeError):
        cwrap.check_for_end()


def test_exhausted_advance_pos():
    with CodeWrapper("", False) as cwrap:
        assert cwrap._advance_pos() is False


def test_premature_validate_type():
    cwrap = CodeWrapper("", False)
    with pytest.raises(RuntimeError):
        cwrap._validate_type(CharacterType.LETTER)


def test_exhausted_validate_type():
    with CodeWrapper("", False) as cwrap:
        assert cwrap._validate_type(CharacterType.LETTER) is False


def test_premature_try_next():
    cwrap = CodeWrapper("")
    with pytest.raises(RuntimeError):
        cwrap.try_next()


def test_exhausted_try_next():
    with CodeWrapper("", False) as cwrap:
        assert cwrap.try_next() is False


def test_invalid_try_next_both():
    with ExitStack() as stack:
        stack.enter_context(pytest.raises(ValueError))
        cwrap: CodeWrapper = stack.enter_context(CodeWrapper("a", False))
        cwrap.try_next(next_char="a", next_type=CharacterType.LETTER)


def test_invalid_try_next_neither():
    with ExitStack() as stack:
        stack.enter_context(pytest.raises(ValueError))
        cwrap: CodeWrapper = stack.enter_context(CodeWrapper("a", False))
        cwrap.try_next()


def test_invalid_try_next_char():
    with CodeWrapper("a", False) as cwrap:
        assert cwrap.try_next(next_char="b") is False


@pytest.mark.parametrize(
    "codeblock,char_type",
    [
        ("0", CharacterType.LETTER),
        ("a", CharacterType.DIGIT),
        ('"', CharacterType.STRING_CHAR),
        ("#", CharacterType.DATE_CHAR),
        ("[", CharacterType.ID_NAME_CHAR),
        ("]", CharacterType.ID_NAME_CHAR),
        ("&", CharacterType.HEX_DIGIT),
        ("H", CharacterType.HEX_DIGIT),
        ("&", CharacterType.OCT_DIGIT),
        ("\r", CharacterType.WS),
        ("\n", CharacterType.WS),
        ("&", CharacterType.ID_TAIL),
    ],
)
def test_invalid_try_next_type(codeblock: str, char_type: CharacterType):
    with CodeWrapper(codeblock, False) as cwrap:
        assert cwrap.try_next(next_type=char_type) is False


def test_valid_try_next_char():
    with CodeWrapper("a", False) as cwrap:
        assert cwrap.try_next(next_char="a") is True


@pytest.mark.parametrize(
    "codeblock,char_type",
    [
        ("a", CharacterType.LETTER),
        ("0", CharacterType.DIGIT),
        ("a", CharacterType.STRING_CHAR),
        ("/", CharacterType.DATE_CHAR),
        ("%", CharacterType.ID_NAME_CHAR),
        ("0", CharacterType.HEX_DIGIT),
        ("f", CharacterType.HEX_DIGIT),
        ("7", CharacterType.OCT_DIGIT),
        (" ", CharacterType.WS),
        ("a", CharacterType.ID_TAIL),
        ("0", CharacterType.ID_TAIL),
        ("_", CharacterType.ID_TAIL),
    ],
)
def test_valid_try_next_type(codeblock: str, char_type: CharacterType):
    with CodeWrapper(codeblock, False) as cwrap:
        assert cwrap.try_next(next_type=char_type) is True


def test_premature_assert_next():
    cwrap = CodeWrapper("")
    with pytest.raises(RuntimeError):
        cwrap.assert_next()


def test_exhausted_assert_next():
    with ExitStack() as stack:
        stack.enter_context(pytest.raises(RuntimeError))
        cwrap: CodeWrapper = stack.enter_context(CodeWrapper("", False))
        cwrap.assert_next()


def test_invalid_assert_next_both():
    with ExitStack() as stack:
        stack.enter_context(pytest.raises(ValueError))
        cwrap: CodeWrapper = stack.enter_context(CodeWrapper("a", False))
        cwrap.assert_next(next_char="a", next_type=CharacterType.LETTER)


def test_invalid_assert_next_neither():
    with ExitStack() as stack:
        stack.enter_context(pytest.raises(ValueError))
        cwrap: CodeWrapper = stack.enter_context(CodeWrapper("a", False))
        cwrap.assert_next()


def test_invalid_assert_next_char():
    with ExitStack() as stack:
        stack.enter_context(pytest.raises(AssertionError))
        cwrap: CodeWrapper = stack.enter_context(CodeWrapper("a", False))
        cwrap.assert_next(next_char="b")


@pytest.mark.parametrize(
    "codeblock,char_type",
    [
        ("0", CharacterType.LETTER),
        ("a", CharacterType.DIGIT),
        ('"', CharacterType.STRING_CHAR),
        ("#", CharacterType.DATE_CHAR),
        ("[", CharacterType.ID_NAME_CHAR),
        ("]", CharacterType.ID_NAME_CHAR),
        ("&", CharacterType.HEX_DIGIT),
        ("H", CharacterType.HEX_DIGIT),
        ("&", CharacterType.OCT_DIGIT),
        ("\r", CharacterType.WS),
        ("\n", CharacterType.WS),
        ("&", CharacterType.ID_TAIL),
    ],
)
def test_invalid_assert_next_type(codeblock: str, char_type: CharacterType):
    with ExitStack() as stack:
        stack.enter_context(pytest.raises(AssertionError))
        cwrap: CodeWrapper = stack.enter_context(CodeWrapper(codeblock, False))
        cwrap.assert_next(next_type=char_type)


def test_valid_assert_next_char():
    with CodeWrapper("a", False) as cwrap:
        assert cwrap.assert_next(next_char="a") is False  # end of codeblock


@pytest.mark.parametrize(
    "codeblock,char_type",
    [
        ("a", CharacterType.LETTER),
        ("0", CharacterType.DIGIT),
        ("a", CharacterType.STRING_CHAR),
        ("/", CharacterType.DATE_CHAR),
        ("%", CharacterType.ID_NAME_CHAR),
        ("0", CharacterType.HEX_DIGIT),
        ("f", CharacterType.HEX_DIGIT),
        ("7", CharacterType.OCT_DIGIT),
        (" ", CharacterType.WS),
        ("a", CharacterType.ID_TAIL),
        ("0", CharacterType.ID_TAIL),
        ("_", CharacterType.ID_TAIL),
    ],
)
def test_valid_assert_next_type(codeblock: str, char_type: CharacterType):
    with CodeWrapper(codeblock, False) as cwrap:
        assert cwrap.assert_next(next_type=char_type) is False  # end of codeblock
