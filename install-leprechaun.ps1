$datadir = "$env:LOCALAPPDATA\leprechaun"
$exepath = "$datadir\leprechaun.exe"
$execlipath = "$datadir\leprechaun-cli.exe"
$exeurl = "https://github.com/andreasxp/leprechaun/releases/download/0.2.0/leprechaun.zip"

$currentUser = New-Object Security.Principal.WindowsPrincipal $([Security.Principal.WindowsIdentity]::GetCurrent())
$elevated = $currentUser.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)

if (!(Test-Path $exepath)) {
    if (!$Silent) { Write-Host -NoNewline "Downloading Leprechaun..." }
    New-Item $datadir -ItemType Directory -Force
    $tmp = New-TemporaryFile | Rename-Item -NewName { $_ -replace 'tmp$', 'zip' } -PassThru
    Invoke-WebRequest -OutFile $tmp $exeurl
    $tmp | Expand-Archive -DestinationPath $datadir -Force
    $tmp | Remove-Item
    if (!$Silent) { Write-Host " Done!" }
} else {
    if (!$Silent) { Write-Host "Leprechaun is already downloaded." }
}

# ======================================================================================================================
$needConfig = $false
$needElevation = $false

# Shortcuts, done in this script
$title    = "Would you like to create a shortcut in start menu and on the desktop?"
$description = "If you add a shortcut, Leprechaun will be accessible in Windows search."
$choices  = "&Yes", "&No"
$argShortcuts = ""
$decision = $Host.UI.PromptForChoice($title, $description, $choices, 0)
if ($decision -eq 0) {
    $needConfig = $true
    $argShortcuts = "--add-shortcuts"
}

# Startup, done in nested launch with priveleges
$title    = "Would you like Leprechaun to run at startup?"
$description = "A scheduled task will be created to run Leprechaun with administrative priveleges."
$choices  = "&Yes", "&No"
$argStartupTask = ""
$decision = $Host.UI.PromptForChoice($title, $description, $choices, 0)
if ($decision -eq 0) {
    $needConfig = $true
    $argStartupTask = "--add-scheduled-task"

    if (!$elevated) {
        $needElevation = $true
    }
}

# Security Exception
$title    = "Add Windows Security exception for the application folder?"
$description = "If you answer 'No', Microsoft Defender might flag some executables as crypto miners."
$choices  = "&Yes", "&No"
$argSecurityException = ""
$decision = $Host.UI.PromptForChoice($title, $description, $choices, 0)
if ($decision -eq 0) {
    $needConfig = $true
    $argSecurityException = "--add-security-exception"

    if (!$elevated) {
        $needElevation = $true
    }
}

# Config run
if ($needConfig) {
    if ($needElevation) {
        $p = Start-Process $execlipath `
            -Wait -PassThru `
            -Verb RunAs `
            -ArgumentList "config $argShortcuts $argStartupTask $argSecurityException"
    } else {
        $p = Start-Process $execlipath `
            -Wait -PassThru `
            -ArgumentList "config $argShortcuts $argStartupTask $argSecurityException"
    }

    if ($p.ExitCode -ne 0) {
        Write-Host "There has been an error during installation."
        exit 1
    }
}
