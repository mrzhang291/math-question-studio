param(
    [Parameter(Mandatory = $true)]
    [string]$Root
)

Add-Type -AssemblyName System.Windows.Forms

$rootPath = [System.IO.Path]::GetFullPath($Root)
$defaultPath = Join-Path $rootPath 'output'
$launcher = Join-Path $rootPath '一键启动教师工作台.bat'
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = 'Select a prepared *_structured question bank folder.'
$dialog.ShowNewFolderButton = $false
if (Test-Path -LiteralPath $defaultPath) {
    $dialog.SelectedPath = $defaultPath
}

try {
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        exit 2
    }
    $bank = $dialog.SelectedPath
    $reviewIndex = Join-Path $bank 'review\index.html'
    $tagArtifact = Join-Path $bank 'tags\all_question_tags.json'
    if (-not (Test-Path -LiteralPath $reviewIndex) -or -not (Test-Path -LiteralPath $tagArtifact)) {
        [System.Windows.Forms.MessageBox]::Show(
            'The selected folder is not a prepared question bank. Please select a *_structured folder containing review\index.html and tags\all_question_tags.json.',
            'Invalid question bank',
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Warning
        ) | Out-Null
        exit 1
    }
    & $launcher $bank
    exit $LASTEXITCODE
}
finally {
    $dialog.Dispose()
}
