
import templateer

def test_env_variables():
    SAMPLE_TEMPLATE = """<@@OS_ENV1@@>"""

    result = templateer.env_variables(SAMPLE_TEMPLATE, {'OS_ENV1': 'test'})

    assert result == '<OS_ENV1>'
