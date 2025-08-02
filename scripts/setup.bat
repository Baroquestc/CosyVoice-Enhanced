@echo off
setlocal enabledelayedexpansion

pushd %~dp0..

echo "Checking Conda installation..."

:: Check if conda is installed
where conda >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo "Conda is not installed or not added to PATH environment variable."
    echo "Please install Anaconda or Miniconda, then run this script."
    exit /b 1
)

echo "Conda is installed, preparing to set up the environment..."

:: Initialize conda command line
call conda activate base

:: Set environment variables to ensure the environment is created in the current directory
set ENV_DIR=%CD%\env

:: Check if environment already exists
if exist "%ENV_DIR%" (
    echo "Environment folder already exists: %ENV_DIR%"
    echo "Activating existing environment..."
    call conda activate "%ENV_DIR%"
) else (
    :: Create environment
    echo "Creating Conda environment at: %ENV_DIR%..."
    call conda create --prefix "%ENV_DIR%" python=3.10 -y

    if %ERRORLEVEL% neq 0 (
        echo "Failed to create environment. Please check error messages."
        exit /b 1
    )

    echo "Environment created successfully!"

    :: Activate the new environment
    echo "Activating environment..."
    call conda activate "%ENV_DIR%"
)

:: Install pynini package
echo Installing pynini 2.1.5...
call conda install -y -c conda-forge pynini==2.1.5

:: Install pyloudnorm package
echo Installing pyloudnorm...
call pip install pyloudnorm

:: Install dependencies from requirements.txt
echo "Installing dependencies from requirements.txt using Aliyun mirror..."
call "%ENV_DIR%\Scripts\pip" install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com

echo.
echo "Dependencies installation completed!"

:: Check if git is installed
echo "Checking git and git lfs..."
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo "Git is not installed or not added to PATH environment variable."
    echo "Please install Git then run this script again."
    exit /b 1
)

:: Check if git lfs is installed
git lfs version >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo "Git LFS is not installed or not initialized."
    echo "Please install Git LFS (https://git-lfs.github.com/) then run this script again."
    exit /b 1
)

:: Create models directory
echo "Checking and creating models directory..."
if not exist "pretrained_models" (
    mkdir pretrained_models
)

:: Check and download models
echo "Checking if models exist..."

:: Define model list
set MODELS[0]=CosyVoice2-0.5B
set MODELS[1]=CosyVoice-300M
set MODELS[2]=CosyVoice-300M-SFT
set MODELS[3]=CosyVoice-300M-Instruct
set MODELS[4]=CosyVoice-ttsfrd

:: Loop to check and download
for /L %%i in (0,1,4) do (
    set MODEL_NAME=!MODELS[%%i]!
    if not exist "pretrained_models\!MODEL_NAME!" (
        echo "Model !MODEL_NAME! does not exist, downloading..."
        git clone https://www.modelscope.cn/iic/!MODEL_NAME!.git pretrained_models/!MODEL_NAME!
        if !ERRORLEVEL! neq 0 (
            echo "Failed to download !MODEL_NAME!. Please check your network connection and git settings."
            echo "You can download it manually later: git clone https://www.modelscope.cn/iic/!MODEL_NAME!.git pretrained_models/!MODEL_NAME!"
        ) else (
            echo "Successfully downloaded !MODEL_NAME!."
        )
    ) else (
        echo "Model !MODEL_NAME! already exists, skipping download."
    )
)

echo.
echo "All models check/download completed!"

:: Run WebUI
echo "Starting WebUI..."
"%ENV_DIR%\python.exe" api\webui.py --port 50000 --model_dir pretrained_models/CosyVoice-300M

echo.
echo "Usage:"
echo "Activate environment: conda activate %ENV_DIR%"
echo "Or: conda activate ./env"
echo.
echo "Deactivate environment: conda deactivate"
echo.
echo "Environment is already activated, ready to use."

popd
endlocal 