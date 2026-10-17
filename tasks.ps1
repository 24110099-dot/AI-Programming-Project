param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("setup", "setup-env", "check-env", "index", "demo", "chat", "eval", "probe", "host2", "server", "test", "clean")]
    [string]$Target
)
$ErrorActionPreference = "Stop"
function Invoke-Uv {
    param([string[]]$UvArgs)
    & uv @UvArgs
    if ($LASTEXITCODE -ne 0) { throw "uv failed: $LASTEXITCODE" }
}
Push-Location $PSScriptRoot
try {
    switch ($Target) {
        "setup"     { Invoke-Uv -UvArgs @("sync"); Invoke-Uv -UvArgs @("run", "python", "-m", "policy_agent.rag.build_index") }
        "setup-env" { Invoke-Uv -UvArgs @("sync", "--locked") }
        "check-env" { Invoke-Uv -UvArgs @("run", "python", "scripts/check_environment.py") }
        "index"     { Invoke-Uv -UvArgs @("run", "python", "-m", "policy_agent.rag.build_index") }
        "demo"      { Invoke-Uv -UvArgs @("run", "python", "scripts/demo.py") }
        "chat"      { Invoke-Uv -UvArgs @("run", "python", "scripts/chat.py") }
        "eval"      { Invoke-Uv -UvArgs @("run", "python", "-m", "policy_agent.eval.run_eval", "--mode", "both") }
        "probe"     { Invoke-Uv -UvArgs @("run", "python", "scripts/probe_server.py") }
        "host2"     { Invoke-Uv -UvArgs @("run", "python", "scripts/second_host.py") }
        "server"    { Invoke-Uv -UvArgs @("run", "python", "-m", "policy_agent.mcp_server.server") }
        "test"      { Invoke-Uv -UvArgs @("run", "pytest", "-q") }
        "clean"     { Remove-Item -Recurse -Force data/index -ErrorAction SilentlyContinue }
    }
} finally { Pop-Location }
