param(
    [switch]$NonInteractive = $false,
    [switch]$Silent,
    [switch]$Shortcuts,
    [switch]$StartupTask,
    [switch]$SecurityException
)

$datadir = "$env:LOCALAPPDATA\leprechaun"
$exepath = "$datadir\leprechaun.exe"
$exeurl = "https://github.com/andreasxp/leprechaun/releases/download/0.2.0/leprechaun.zip"

function Set-Shortcuts {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Start Menu\Programs\Leprechaun Miner.lnk")
    $Shortcut.TargetPath = $exepath
    $Shortcut.Save()
}

function Set-StartupTask {
    $taskName = "Start Leprechaun Miner"

    $action = New-ScheduledTaskAction -Execute $exepath
    $trigger = New-ScheduledTaskTrigger -AtLogOn

    Register-ScheduledTask -Action $action -Trigger $trigger -TaskName $taskName -Description "Start Leprechaun Miner." -RunLevel Highest
}

function Set-SecurityException {
    Add-MpPreference -ExclusionPath $datadir
}

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

if ($NonInteractive) {
    if (($StartupTask -or $SecurityException) -and !$elevated) {
        Write-Host "Error: missing administrative priveleges"
        exit 1
    }

    if ($Shortcuts) { Set-Shortcuts }
    if ($StartupTask) { Set-StartupTask }
    if ($SecurityException) { Set-SecurityException }

} else {
    # Some actions might need administrative priveleges in a new script run
    $needAdminRun = $false

    # Shortcuts, done in this script
    $title    = "Would you like to create a shortcut in start menu and on the desktop?"
    $description = "If you add a shortcut, Leprechaun will be accessible in Windows search."
    $choices  = "&Yes", "&No"
    $decision = $Host.UI.PromptForChoice($title, $description, $choices, 0)
    if ($decision -eq 0) { Set-Shortcuts }

    # Startup, done in nested launch with priveleges
    $title    = "Would you like Leprechaun to run at startup?"
    $description = "A scheduled task will be created to run Leprechaun with administrative priveleges."
    $choices  = "&Yes", "&No"
    $decision = $Host.UI.PromptForChoice($title, $description, $choices, 0)
    $flagStartupTask = ""
    if ($decision -eq 0) {
        if ($elevated) {
            Set-StartupTask
        } else {
            $needAdminRun = $true
            $flagStartupTask = "StartupTask"
        }
    }

    # Security Exception
    $title    = "Add Windows Security exception for the application folder?"
    $description = "If you answer 'No', Microsoft Defender might flag some executables as crypto miners."
    $choices  = "&Yes", "&No"
    $decision = $Host.UI.PromptForChoice($title, $description, $choices, 0)
    $flagSecurityException = ""
    if ($decision -eq 0) {
        if ($elevated) {
            Set-SecurityException
        } else {
            $needAdminRun = $true
            $flagSecurityException = "-SecurityException"
        }
    }

    # Second admin run
    if ($needAdminRun) {
        $p = Start-Process powershell.exe `
            -WindowStyle Hidden `
            -Wait -PassThru `
            -Verb RunAs `
            -ArgumentList "-NoProfile -File `"$PSCommandPath`" -NonInteractive -Silent $flagStartupTask $flagSecurityException"
        
        if ($p.ExitCode -ne 0) {
            Write-Host "There has been an error during installation."
            exit 1
        }
    }
}
