#!/usr/bin/env julia
"""
GapsCLI.jl — Rural Peds Gap Analysis Standard v1.0
Local command-line tool for managing GAPS.md files.

Usage:
    julia GapsCLI.jl list                          # List all active gaps
    julia GapsCLI.jl list --priority P0            # Filter by priority
    julia GapsCLI.jl list --category content       # Filter by category
    julia GapsCLI.jl add "Title" --priority P1 --category content [--notes "..."]
    julia GapsCLI.jl close GAP-001 --pr 42         # Move to Completed
    julia GapsCLI.jl next                          # Show next gap to work on (P0 first)
    julia GapsCLI.jl stats                         # Summary counts
    julia GapsCLI.jl help                          # Show this help

Install (add to PATH):
    ln -s $(pwd)/julia/GapsCLI.jl ~/bin/gap
    chmod +x ~/bin/gap
"""

using Dates

const GAPS_FILE = "GAPS.md"
const SPEC_URL = "https://github.com/ruralpeds/gap-analysis-standard/blob/main/SPEC.md"

# ── ANSI colors ───────────────────────────────────────────────────────────────

const RED     = "\033[31m"
const YELLOW  = "\033[33m"
const GREEN   = "\033[32m"
const CYAN    = "\033[36m"
const BOLD    = "\033[1m"
const RESET   = "\033[0m"

priority_color(p) = p == "P0" ? RED :
                    p == "P1" ? YELLOW :
                    p == "P2" ? GREEN :
                    CYAN

# ── Row parsing ───────────────────────────────────────────────────────────────

struct GapRow
    id::String
    title::String
    priority::String
    category::String
    created::String
    notes::String
end

function parse_active_row(line::AbstractString)::Union{GapRow, Nothing}
    m = match(r"^\|\s*(GAP-\d+)\s*\|(.+)$", strip(line))
    isnothing(m) && return nothing
    id = strip(m[1])
    startswith(id, "ID") && return nothing  # header row
    parts = [strip(p) for p in split(m[2], "|")]
    length(parts) < 5 && append!(parts, fill("", 5 - length(parts)))
    GapRow(id, parts[1], parts[2], parts[3], parts[4], get(parts, 5, ""))
end

function read_gaps(file::String = GAPS_FILE)::Vector{GapRow}
    isfile(file) || error("$file not found. Run `gap init` or bootstrap-gaps.sh first.")
    text = read(file, String)
    active_section = match(r"## Active\n(.*?)(?=\n## |\z)"s, text)
    isnothing(active_section) && return GapRow[]
    rows = GapRow[]
    for line in split(active_section[1], "\n")
        row = parse_active_row(line)
        isnothing(row) || push!(rows, row)
    end
    rows
end

function next_id(file::String = GAPS_FILE)::String
    text = isfile(file) ? read(file, String) : ""
    ids = [parse(Int, m[1]) for m in eachmatch(r"GAP-(\d+)", text)]
    n = isempty(ids) ? 0 : maximum(ids)
    "GAP-$(lpad(n + 1, 3, '0'))"
end

# ── Commands ──────────────────────────────────────────────────────────────────

function cmd_list(args)
    rows = read_gaps()
    filter_priority = get(Dict(args), "--priority", nothing)
    filter_category = get(Dict(args), "--category", nothing)

    if !isnothing(filter_priority)
        rows = filter(r -> r.priority == uppercase(filter_priority), rows)
    end
    if !isnothing(filter_category)
        rows = filter(r -> r.category == lowercase(filter_category), rows)
    end

    if isempty(rows)
        println("$(GREEN)No active gaps match your filter.$(RESET)")
        return
    end

    # Sort by priority (P0 first), then by ID
    priority_order = Dict("P0" => 0, "P1" => 1, "P2" => 2, "P3" => 3)
    sort!(rows, by = r -> (get(priority_order, r.priority, 9), r.id))

    println("\n$(BOLD)Active Gaps — $(GAPS_FILE)$(RESET)\n")
    println("  $(BOLD)$(lpad("ID", 8))  $(lpad("Pri", 4))  $(rpad("Category", 14))  Title$(RESET)")
    println("  " * "─"^70)
    for r in rows
        pc = priority_color(r.priority)
        println("  $(CYAN)$(lpad(r.id, 8))$(RESET)  $(pc)$(lpad(r.priority, 4))$(RESET)  $(rpad(r.category, 14))  $(r.title)")
        isempty(r.notes) || println("  $(lpad("", 8))  $(lpad("", 4))  $(lpad("", 14))  $(BOLD)↳ $(r.notes)$(RESET)")
    end
    println()
    println("  $(length(rows)) gap(s) shown. Spec: $(SPEC_URL)")
    println()
end

function cmd_add(args)
    length(args) < 1 && error("Usage: gap add \"Title\" --priority P1 --category content [--notes \"...\"]")
    arg_dict = Dict{String,String}()
    title = ""
    i = 1
    while i <= length(args)
        if startswith(args[i], "--")
            arg_dict[args[i]] = get(args, i + 1, "")
            i += 2
        else
            title = args[i]
            i += 1
        end
    end
    isempty(title) && error("Title is required.")
    length(title) > 60 && @warn "Title exceeds 60 characters ($(length(title))). Spec recommends ≤60."

    priority = get(arg_dict, "--priority", "P2")
    category = get(arg_dict, "--category", "general")
    notes    = get(arg_dict, "--notes", "")
    today    = string(today())
    id       = next_id()

    valid_priorities = ["P0", "P1", "P2", "P3"]
    uppercase(priority) ∉ valid_priorities && error("Priority must be one of: $(join(valid_priorities, ", "))")

    new_row = "| $(id) | $(title) | $(uppercase(priority)) | $(lowercase(category)) | $(today) | $(notes) |\n"

    text = read(GAPS_FILE, String)
    # Insert after the Active table header row
    header_pattern = r"(\| ID \| Title \| Priority \| Category \| Created \| Notes \|\n\|[-| ]+\|\n)"
    if occursin(header_pattern, text)
        text = replace(text, header_pattern => SubstitutionString("\\1$(new_row)"))
        write(GAPS_FILE, text)
        println("$(GREEN)✓ Added $(id): $(title)$(RESET)")
    else
        error("Could not find Active table header in $(GAPS_FILE). Is it formatted correctly?")
    end
end

function cmd_next(args)
    rows = read_gaps()
    isempty(rows) && (println("$(GREEN)No active gaps. 🎉$(RESET)"); return)

    priority_order = Dict("P0" => 0, "P1" => 1, "P2" => 2, "P3" => 3)
    sort!(rows, by = r -> (get(priority_order, r.priority, 9), r.id))
    r = first(rows)
    pc = priority_color(r.priority)
    println("\n$(BOLD)Next gap to work on:$(RESET)\n")
    println("  $(CYAN)$(r.id)$(RESET)  $(pc)$(r.priority)$(RESET)  [$(r.category)]  $(r.title)")
    isempty(r.notes) || println("  Notes: $(r.notes)")
    println("\n  When done: include $(BOLD)Closes $(r.id)$(RESET) in your PR body.")
    println()
end

function cmd_stats(args)
    rows = read_gaps()
    text = read(GAPS_FILE, String)

    completed_ids = [m[1] for m in eachmatch(r"(GAP-\d+)", split(text, "## Completed")[end])]
    n_completed = length(unique(completed_ids))

    by_priority = Dict(p => count(r -> r.priority == p, rows) for p in ["P0", "P1", "P2", "P3"])
    by_category = Dict{String,Int}()
    for r in rows
        by_category[r.category] = get(by_category, r.category, 0) + 1
    end

    println("\n$(BOLD)Gap Stats — $(GAPS_FILE)$(RESET)\n")
    println("  Active:    $(length(rows))")
    println("  Completed: $(n_completed)")
    println()
    println("  $(BOLD)By Priority:$(RESET)")
    for p in ["P0", "P1", "P2", "P3"]
        n = get(by_priority, p, 0)
        n > 0 && println("    $(priority_color(p))$(p)$(RESET)  $(n)")
    end
    println()
    println("  $(BOLD)By Category:$(RESET)")
    for (cat, n) in sort(collect(by_category), by = x -> -x[2])
        println("    $(rpad(cat, 16))  $(n)")
    end
    println()
end

function cmd_help(args)
    println("""
$(BOLD)gap — Rural Peds Gap Analysis Standard v1.0$(RESET)
$(SPEC_URL)

$(BOLD)Commands:$(RESET)
  list                          List all active gaps (sorted P0 → P3)
  list --priority P0            Filter by priority (P0/P1/P2/P3)
  list --category content       Filter by category
  add "Title" [options]         Add a new gap to GAPS.md
    --priority P1               Priority (default: P2)
    --category content          Category (default: general)
    --notes "Optional context"  Notes (≤120 chars)
  next                          Show the highest-priority gap to work on
  stats                         Summary counts by priority and category
  help                          Show this help

$(BOLD)Workflow:$(RESET)
  1. gap list              — see what needs doing
  2. gap next              — pick the top item
  3. ... do the work ...
  4. Open a PR with "Closes GAP-NNN" in the PR body
  5. Merge → the gap-lifecycle Action auto-moves it to Completed
""")
end

# ── Entry point ───────────────────────────────────────────────────────────────

function main()
    args = ARGS
    isempty(args) && (cmd_list(String[]); return)

    cmd = lowercase(args[1])
    rest = args[2:end]

    cmd == "list"  && cmd_list(rest)
    cmd == "add"   && cmd_add(rest)
    cmd == "next"  && cmd_next(rest)
    cmd == "stats" && cmd_stats(rest)
    cmd == "help"  && cmd_help(rest)
    cmd ∉ ["list", "add", "next", "stats", "help"] &&
        println("$(RED)Unknown command: $(cmd). Run `gap help`.$(RESET)")
end

main()
