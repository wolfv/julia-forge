# julia-forge

Repackages official Julia binary releases as conda packages, built with
[rattler-build](https://github.com/prefix-dev/rattler-build) and published to
[prefix.dev](https://prefix.dev) channels.

Version tracking mirrors [juliaup](https://github.com/JuliaLang/juliaup)'s
channel model: `scripts/update_recipe.py` resolves a juliaup channel
(`release` or `lts`) to a concrete Julia version via juliaup's hosted
versiondb, and looks up the per-platform download URL/sha256 from the same
upstream `versions.json` juliaup's own version-db generator consumes.

## Using Julia with Pixi

Create a Pixi workspace, add `julia-forge` ahead of conda-forge in the channel
list, and add Julia:

```shell
pixi init my-julia-project
cd my-julia-project
pixi workspace channel add --prepend https://prefix.dev/julia-forge
pixi add julia
```

Run Julia without manually activating the environment:

```shell
pixi run julia --version
pixi run julia
```

Alternatively, `pixi shell` activates the environment and makes `julia`
available directly. The resulting `pixi.toml` will look roughly like this:

```toml
[workspace]
channels = ["https://prefix.dev/julia-forge", "conda-forge"]
platforms = ["linux-64"] # Pixi selects the platform during `pixi init`

[dependencies]
julia = ">=1.12,<1.13"
```

Julia packages continue to be managed by Julia's native package manager. A
Julia `Project.toml` and `Manifest.toml` can live alongside `pixi.toml`:

```shell
pixi run julia --project=. -e 'using Pkg; Pkg.add("DataFrames")'
pixi run julia --project=. -e 'using DataFrames; println("DataFrames loaded")'
```

Pixi then locks the Julia executable and other conda dependencies in
`pixi.lock`, while Julia locks its packages in `Project.toml` and
`Manifest.toml`.

### Selecting the release or LTS series

An unpinned `pixi add julia` selects the latest stable release. To use the
current Julia 1.10 LTS series, add an explicit version constraint instead:

```shell
pixi add "julia=1.10.*"
```

The `julia-forge` channel contains both release and LTS builds. The separate
`julia-forge-lts` channel is retained as a convenience for environments that
should only see LTS builds. Do not add both custom channels to one workspace;
use `julia-forge` with a version constraint when both series need to remain
available to the solver.

Packages are currently built for `linux-64`, `linux-aarch64`, `osx-arm64`,
and `win-64`.

## Updating recipes

```
pixi run update-recipe-release
pixi run update-recipe-lts
```

Each is a no-op if the recipe is already at the version its juliaup channel
currently points to. `.github/workflows/update-recipe.yml` runs both on a
schedule and opens a PR when either channel has moved forward.
