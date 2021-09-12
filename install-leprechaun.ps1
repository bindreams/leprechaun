$datadir = "$env:LOCALAPPDATA\leprechaun"
$exepath = "$datadir\leprechaun.exe"
$exeurl = "https://github.com/andreasxp/leprechaun/releases/download/0.5.1/leprechaun.zip"

$currentUser = New-Object Security.Principal.WindowsPrincipal $([Security.Principal.WindowsIdentity]::GetCurrent())
$elevated = $currentUser.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)

Write-Host -NoNewline "Downloading Leprechaun... "
New-Item $datadir -ItemType Directory -Force > $null
$tmp = New-TemporaryFile | Rename-Item -NewName { $_ -replace 'tmp$', 'zip' } -PassThru
Invoke-WebRequest -OutFile $tmp $exeurl
$tmp | Expand-Archive -DestinationPath $datadir -Force
$tmp | Remove-Item
Write-Host "Done!" -Foreground Green

# ======================================================================================================================
$needElevation = $false

# Shortcuts, done in this script
$title    = "Would you like to create a shortcut on the Desktop?"
$description = "If you answer 'No', Leprechaun will still be accessible from the Start Menu."
$choices  = "&Yes", "&No"
$argShortcut = ""
$decision = $Host.UI.PromptForChoice($title, $description, $choices, 0)
if ($decision -eq 0) {
    $argShortcut = "--add-desktop-shortcut"
}

# Startup, done in nested launch with priveleges
$title    = "Would you like Leprechaun to run at startup?"
$description = "A scheduled task will be created to run Leprechaun with administrative priveleges."
$choices  = "&Yes", "&No"
$argStartupTask = ""
$decision = $Host.UI.PromptForChoice($title, $description, $choices, 0)
if ($decision -eq 0) {
    $argStartupTask = "--add-scheduled-task"

    if (!$elevated) {
        $needElevation = $true
    }
}

# Security Exception
$title    = "Add Windows Security exception for the application folder?"
$description = "If you answer 'No', your antivirus might quarantine or delete crypto mining executables."
$choices  = "&Yes", "&No"
$argSecurityException = ""
$decision = $Host.UI.PromptForChoice($title, $description, $choices, 0)
if ($decision -eq 0) {
    $argSecurityException = "--add-security-exception"

    if (!$elevated) {
        $needElevation = $true
    }
}

Write-Host ""
Write-Host -NoNewline "Installing Leprechaun... "

# Config run
if ($needElevation) {
    $p = Start-Process $exepath `
        -WindowStyle Hidden `
        -Wait -PassThru `
        -Verb RunAs `
        -ArgumentList "config --add-start-shortcut $argShortcut $argStartupTask $argSecurityException"
} else {
    $p = Start-Process $exepath `
        -WindowStyle Hidden `
        -Wait -PassThru `
        -ArgumentList "config --add-start-shortcut $argShortcut $argStartupTask $argSecurityException"
}

if ($p.ExitCode -ne 0) {
    Write-Host "Error" -Foreground Red
    Write-Host ("There has been an error during installation. Error code: {0}" -f $p.ExitCode) -Foreground Red
    exit 1
}

Write-Host "Done!" -Foreground Green