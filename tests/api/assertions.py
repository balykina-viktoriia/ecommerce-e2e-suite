from jsonschema import Draft202012Validator, FormatChecker


def assert_matches_schema(body, schema: dict):
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(body),
        key=str,
    )
    assert not errors, "Response does not match schema:\n" + "\n".join(
        f"- {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in errors
    )
