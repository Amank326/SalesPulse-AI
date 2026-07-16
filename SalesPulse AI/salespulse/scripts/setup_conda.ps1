<#
Run this PowerShell script to create a Conda environment with prebuilt packages (recommended on Windows).
Usage (PowerShell):
  .\scripts\setup_conda.ps1

This script requires `conda` (Anaconda or Miniconda) to be installed and available in PATH.
#>

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Host "Conda not found. Install Miniconda or Anaconda first: https://docs.conda.io/en/latest/miniconda.html" -ForegroundColor Yellow
    exit 1
}

$envName = 'salespulse'
Write-Host "Creating Conda env '$envName' with Python 3.11 and core packages..." -ForegroundColor Cyan
conda create -n $envName python=3.11 -y

Write-Host "Activating env and installing packages from conda-forge..." -ForegroundColor Cyan
conda activate $envName
conda install -y -c conda-forge pandas=2.2.2 numpy=1.26.4 scikit-learn=1.5.0 matplotlib joblib openpyxl

Write-Host "Installing remaining Python packages via pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn python-multipart python-dotenv httpx

Write-Host "Done. To activate the environment later: conda activate $envName" -ForegroundColor Green
