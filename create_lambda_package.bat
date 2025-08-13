@echo off
echo Creating AWS Lambda deployment package...

REM Create deployment directory
if exist lambda_deployment rmdir /s /q lambda_deployment
mkdir lambda_deployment

REM Copy source code
xcopy /s /e src lambda_deployment\src\

REM Copy essential files
copy lambda_function.py lambda_deployment\
copy requirements.lambda.txt lambda_deployment\
if exist .env copy .env lambda_deployment\

REM Copy documents directory
if exist documents xcopy /s /e documents lambda_deployment\documents\

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.lambda.txt -t lambda_deployment

REM Create ZIP file
echo Creating ZIP file...
cd lambda_deployment
powershell Compress-Archive -Path * -DestinationPath ..\lambda_deployment.zip -Force
cd ..

echo Deployment package created: lambda_deployment.zip
echo Upload this file to AWS Lambda Console
pause

