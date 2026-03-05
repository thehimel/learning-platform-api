# Test Speed Optimizations

Notes on how pytest suite speed was improved.

## What Changed

- Introduced a session-scoped `test_engine` fixture in [conftest.py](../../conftest.py), so the SQLAlchemy engine is created once per test session instead of once per test. Each test still gets its own connection and transaction for isolation.
- Added `pytest-xdist` for parallel execution across CPU cores (`-n auto`). On a small suite the worker spawn overhead and DB connection contention can outweigh the gains; it pays off more as the suite grows or in CI with many cores.
- Use `-q` for quiet mode, which trims output and speeds up I/O slightly.

## Commands

```shell
# Quiet mode (less output, slightly faster)
pytest -q

# Show 10 slowest tests (helps find bottlenecks)
pytest --durations=10

# Parallel execution across CPU cores (pytest-xdist)
pytest -n auto

# Combine: quiet + parallel
pytest -q -n auto
```

Run `pytest --durations=10` to measure timing on your own machine; the numbers here will vary by hardware and suite size.

See [commands.md](../commands.md) for the full pytest and "Faster runs" section.
