param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("setup", "setup-env", "check-env", "test", "probe", "server")]
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
        "setup" { Invoke-Uv -UvArgs @("sync", "--locked") }
        "setup-env" { Invoke-Uv -UvArgs @("sync", "--locked") }
        "check-env" { Invoke-Uv -UvArgs @("run", "--locked", "python", "scripts/check_environment.py") }
        "test" { Invoke-Uv -UvArgs @("run", "--locked", "pytest", "-q", "tests/test_request_store.py", "tests/test_server.py", "tests/test_mcp_client.py", "tests/test_probe.py") }
        "probe" { Invoke-Uv -UvArgs @("run", "--locked", "python", "scripts/probe_server.py") }
        "server" { Invoke-Uv -UvArgs @("run", "--locked", "python", "-m", "policy_agent.mcp_server.server") }
    }
} finally { Pop-Location }
