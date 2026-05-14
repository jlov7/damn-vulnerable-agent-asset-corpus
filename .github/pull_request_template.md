## Summary

<!-- What changed and why? -->

## Fixture Impact

<!-- List affected fixtures or write "none". -->

## Validation

```text
make verify
make pytest-safety
make write-signed
```

## Safety Checklist

- [ ] No fixture payload touches the network.
- [ ] No fixture payload reads real secrets or credential paths.
- [ ] No destructive behavior, persistence, subprocess spawning, or permission changes.
- [ ] No symlinks under `fixtures/**`.
- [ ] No `test_*.py` or `*_test.py` files under `fixtures/**`.
- [ ] Evidence references point to exact local bytes or line ranges.
- [ ] Manifest and scorecard entries are updated.
