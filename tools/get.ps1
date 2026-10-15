# Downloads Squad Ballistics into "Desktop\Squad-Ballistics" and runs setup.
# Usage (PowerShell):
#   irm https://raw.githubusercontent.com/DelineDelorian/Squad-Ballistics/refs/heads/claude/trusting-cray-6sbies/tools/get.ps1 | iex

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$repo = "https://github.com/DelineDelorian/Squad-Ballistics"
$branch = if ($env:SB_BRANCH) { $env:SB_BRANCH } else { "claude/trusting-cray-6sbies" }

$desktop = [Environment]::GetFolderPath("Desktop")
$target = Join-Path $desktop "Squad-Ballistics"

if (Test-Path $target) {
    if (Test-Path (Join-Path $target ".git")) {
        Write-Host "Updating existing folder $target"
        git -C $target fetch origin $branch
        git -C $target checkout $branch
        git -C $target pull --ff-only origin $branch
        & (Join-Path $target "setup.bat")
        return
    }

    # Never delete an existing folder: keep it as a backup.
    $backup = "$target-backup-" + (Get-Date -Format "yyyyMMdd-HHmmss")
    Write-Host "Existing folder moved to $backup"
    Move-Item $target $backup
}

if (Get-Command git -ErrorAction SilentlyContinue) {
    git clone -b $branch "$repo.git" $target
} else {
    $zip = Join-Path $env:TEMP "SquadBallistics-src.zip"
    $extract = Join-Path $env:TEMP "SquadBallistics-src"

    Write-Host "Downloading $branch..."
    Invoke-WebRequest "$repo/archive/refs/heads/$branch.zip" -OutFile $zip -UseBasicParsing

    if (Test-Path $extract) { Remove-Item $extract -Recurse -Force }
    Expand-Archive $zip $extract

    $inner = Get-ChildItem $extract -Directory | Select-Object -First 1
    Move-Item $inner.FullName $target
    Remove-Item $zip, $extract -Recurse -Force
}

Write-Host "Project folder: $target"
& (Join-Path $target "setup.bat")
