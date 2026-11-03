module JuliaForgeExample

export julia_main

function print_help(io::IO=stdout)
    println(io, "Usage: julia-forge-example [NAME ...]")
    println(io, "Print a greeting from a PackageCompiler sysimage.")
end

function julia_main(args=ARGS)::Cint
    if any(arg -> arg in ("-h", "--help"), args)
        print_help()
        return 0
    end

    names = isempty(args) ? ["world"] : args
    println("Hello, ", join(names, ", "), "!")
    println("Running precompiled Julia ", VERSION, " on ", Sys.MACHINE)
    return 0
end

end
