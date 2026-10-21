@echo off
rem universal-modder's um, run from universal-optimizer's environment (it is a dependency).
rem Uses uv when available (set UO_NO_UV=1 to skip it); otherwise python on PATH,
rem which then needs: pip install psutil git+https://github.com/rehan-remade/universal-modder
setlocal
rem The repo root, resolved without a trailing backslash: in "C:\path\" the \" escapes the closing
rem quote for uv and python, which mangles every argument after it. No cd: relative paths stay the caller's.
for %%I in ("%~dp0..") do set "UO_ROOT=%%~fI"
if defined UO_NO_UV goto python
where uv >nul 2>&1 || goto python
uv run --quiet --project "%UO_ROOT%" python -m um %*
exit /b %ERRORLEVEL%

:python
if defined PYTHONPATH (set "PYTHONPATH=%UO_ROOT%;%PYTHONPATH%") else set "PYTHONPATH=%UO_ROOT%"
where python >nul 2>&1 || goto nopython
python -m um %*
exit /b %ERRORLEVEL%

:nopython
echo uo: neither uv nor python is on PATH. Install uv: https://docs.astral.sh/uv/ 1>&2
exit /b 1
