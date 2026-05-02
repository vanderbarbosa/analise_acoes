$ErrorActionPreference = 'SilentlyContinue'
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
Set-Location $projectRoot

git add -A | Out-Null
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    exit 0
}

$ts = Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'
git -c user.email='vander.barbosa@gmail.com' -c user.name='Vanderlei Barbosa' commit -m "auto: $ts Claude session" | Out-Null
git push origin main 2>&1 | Out-Null

exit 0
