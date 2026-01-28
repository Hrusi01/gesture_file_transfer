@echo off
echo Installing dependencies... This may take a few minutes depending on your internet connection.
call venv\Scripts\activate
pip install -r requirements.txt
echo.
echo Installation complete! You can now run the sender and receiver scripts.
pause
