using Libdl
using PackageCompiler

length(ARGS) == 1 || error("usage: build.jl PREFIX")
prefix = abspath(only(ARGS))
source_root = @__DIR__
app_source = joinpath(source_root, "app")
app_dest = joinpath(prefix, "share", "julia-forge-example", "app")
libexec = joinpath(prefix, "libexec", "julia-forge-example")
sysimage = joinpath(libexec, "julia-forge-example." * Libdl.dlext)

mkpath(dirname(app_dest))
mkpath(libexec)
cp(app_source, app_dest; force=true)
cp(joinpath(source_root, "launch.jl"), joinpath(libexec, "launch.jl"); force=true)

create_sysimage(
    [:JuliaForgeExample];
    project=app_source,
    sysimage_path=sysimage,
    precompile_execution_file=joinpath(source_root, "precompile.jl"),
    incremental=true,
    cpu_target="generic",
)

if Sys.iswindows()
    scripts = joinpath(prefix, "Scripts")
    mkpath(scripts)
    wrapper = """@echo off
set "JFE_PREFIX=%~dp0.."
"%JFE_PREFIX%\\Library\\bin\\julia.exe" --startup-file=no --history-file=no -J "%JFE_PREFIX%\\libexec\\julia-forge-example\\julia-forge-example.dll" --project="%JFE_PREFIX%\\share\\julia-forge-example\\app" "%JFE_PREFIX%\\libexec\\julia-forge-example\\launch.jl" %*
exit /b %ERRORLEVEL%
"""
    write(joinpath(scripts, "julia-forge-example.bat"), wrapper)
else
    bindir = joinpath(prefix, "bin")
    mkpath(bindir)
    wrapper = """#!/bin/sh
set -eu
JFE_PREFIX=\$(CDPATH= cd -- "\$(dirname -- "\$0")/.." && pwd)
exec "\$JFE_PREFIX/bin/julia" --startup-file=no --history-file=no -J "\$JFE_PREFIX/libexec/julia-forge-example/julia-forge-example.$(Libdl.dlext)" --project="\$JFE_PREFIX/share/julia-forge-example/app" "\$JFE_PREFIX/libexec/julia-forge-example/launch.jl" "\$@"
"""
    path = joinpath(bindir, "julia-forge-example")
    write(path, wrapper)
    chmod(path, 0o755)
end
