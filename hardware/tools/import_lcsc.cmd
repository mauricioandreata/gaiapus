@echo off
rem Gaiapus - imports footprints + 3D models of every LCSC part from EasyEDA/LCSC.
rem Run on Windows from this folder (double-click or "import_lcsc.cmd"). Needs Python 3 and internet.
rem Output: hardware\lib\lcsc.kicad_sym, hardware\lib\lcsc.pretty\, hardware\lib\lcsc.3dshapes\
rem Then tell Claude "importei" - apply_lcsc.py fixes paths, checks pad numbers and updates the schematic.

python -m pip install --upgrade easyeda2kicad || goto :err
python -m easyeda2kicad --full --overwrite --output "%~dp0..\lib\lcsc" --lcsc_id ^
 C2913206 C5333985 C112011 C161942 C5148694 C2845237 C2909890 C131093 ^
 C13564 C165948 C7519 C2988620 C88374 C160409 ^
 C18221164 C116501 C160402 || goto :err
echo.
echo OK - library written to hardware\lib\lcsc.*
pause
exit /b 0
:err
echo.
echo FAILED - copy the messages above to Claude.
pause
exit /b 1
