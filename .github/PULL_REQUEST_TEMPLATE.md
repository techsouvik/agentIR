## Description

Briefly describe the change, motivation, and context.

Fixes #(issue)

---

## Type of Change

- [ ] `feat`: New feature or framework adapter
- [ ] `fix`: Bug fix
- [ ] `docs`: Documentation improvement
- [ ] `perf`: Performance optimization
- [ ] `refactor`: Internal refactoring with no behavioral change
- [ ] `test`: Adding or updating test suites

---

## Checklist

- [ ] My code follows the project's layered architecture and zero-framework-core rules.
- [ ] I have added tests that prove my fix or feature works (unit, property, golden, CLI).
- [ ] `pytest --cov=agentir` passes with $\ge 80\%$ coverage.
- [ ] `mypy src tests` passes with 0 errors (strict mode).
- [ ] `ruff check .` and `ruff format --check .` pass with 0 errors.
- [ ] I have updated relevant documentation in `docs/` and `README.md` if applicable.
