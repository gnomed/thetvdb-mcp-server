# Manual Tests

These tests are run manually against the live TVDB API. They are not part of the
automated test suite because they require a real API key and make actual HTTP
requests.

## Running

Set the `TVDB_API_KEY` environment variable and run the specific test:

```bash
TVDB_API_KEY=your_key uv run python tests/manual/test_e2e_translations.py
```

## Tests

- **test_e2e_translations.py**: Tests all TVDB endpoints with `result_language='eng'`
  to verify that translation fields are correctly stripped from responses.
