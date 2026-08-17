# julia-forge

Repackages official Julia binary releases as conda packages, built with
[rattler-build](https://github.com/prefix-dev/rattler-build) and published to
[prefix.dev](https://prefix.dev) channels.

Version tracking mirrors [juliaup](https://github.com/JuliaLang/juliaup)'s
channel model: `scripts/update_recipe.py` resolves a juliaup channel
(`release` or `lts`) to a concrete Julia version via juliaup's hosted
versiondb, and looks up the per-platform download URL/sha256 from the same
upstream `versions.json` juliaup's own version-db generator consumes.

## Channels

There are two prefix.dev channels, each hosting a package literally named
`julia` (so anything depending on `julia` resolves correctly regardless of
which one you use) — pick **one**, not both, in the same environment, since
having both channels enabled at once gives the solver two different versions
of the same package name to choose between:

| prefix.dev channel | recipe             | tracks juliaup channel |
|---------------------|--------------------|-------------------------|
| `julia-forge`       | `julia/`           | `release`               |
| `julia-forge-lts`   | `julia-lts/`        | `lts`                   |

## Updating recipes

```
pixi run update-recipe-release
pixi run update-recipe-lts
```

Each is a no-op if the recipe is already at the version its juliaup channel
currently points to. `.github/workflows/update-recipe.yml` runs both on a
schedule and opens a PR when either channel has moved forward.
