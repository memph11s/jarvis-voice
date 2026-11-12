param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$ModelName = "vosk-model-small-ru-0.22"
$ModelDir = Join-Path $Root "models\$ModelName"

& $Python -m venv (Join-Path $Root ".venv")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $VenvPython -m pip install -r (Join-Path $Root "requirements.txt")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not (Test-Path (Join-Path $ModelDir "conf\model.conf"))) {
    $ModelBase = "https://huggingface.co/Derur/vosk-models/resolve/main/stt/ru/$ModelName"
    $ModelFiles = @(
        "README",
        "am/final.mdl",
        "conf/mfcc.conf",
        "conf/model.conf",
        "graph/Gr.fst",
        "graph/HCLr.fst",
        "graph/disambig_tid.int",
        "graph/phones/word_boundary.int",
        "ivector/final.dubm",
        "ivector/final.ie",
        "ivector/final.mat",
        "ivector/global_cmvn.stats",
        "ivector/online_cmvn.conf",
        "ivector/splice.conf"
    )
    foreach ($File in $ModelFiles) {
        $Destination = Join-Path $ModelDir ($File -replace "/", "\")
        New-Item -ItemType Directory -Force -Path (Split-Path $Destination) | Out-Null
        Invoke-WebRequest -Uri "$ModelBase/$File" -OutFile $Destination
    }
}

$PiperDir = Join-Path $Root "models\piper"
$PiperBase = "https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/dmitri/medium"
if (-not (Test-Path (Join-Path $PiperDir "ru_RU-dmitri-medium.onnx"))) {
    New-Item -ItemType Directory -Force -Path $PiperDir | Out-Null
    Invoke-WebRequest -Uri "$PiperBase/ru_RU-dmitri-medium.onnx" -OutFile (Join-Path $PiperDir "ru_RU-dmitri-medium.onnx")
    Invoke-WebRequest -Uri "$PiperBase/ru_RU-dmitri-medium.onnx.json" -OutFile (Join-Path $PiperDir "ru_RU-dmitri-medium.onnx.json")
}

& $VenvPython -m unittest discover -s (Join-Path $Root "tests") -t $Root -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "`nГотово. Запуск: $Root\run.ps1"
