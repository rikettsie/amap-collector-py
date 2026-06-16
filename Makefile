.PHONY: release

PYPROJECT_VERSION := $(shell grep -E '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

release:
	@test -n "$(VERSION)" || (echo "Usage: make release VERSION=x.y.z" && exit 1)
	@test "$(VERSION)" = "$(PYPROJECT_VERSION)" || (echo "Error: VERSION=$(VERSION) does not match pyproject.toml ($(PYPROJECT_VERSION))" && exit 1)
	uv sync
	git add pyproject.toml uv.lock
	git commit -m "chore: bump version to v$(VERSION)"
	git tag v$(VERSION)
	git push origin HEAD
	git push origin v$(VERSION)
