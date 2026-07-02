@echo off
chcp 65001 >nul
setlocal EnableExtensions

rem =====================================================================
rem  migrate_local_cache.bat  (1회용)
rem  루트 재배치(feature/emoi-cluster-v3: 루트 -> src/) 이후,
rem  옛 경로에 남은 gitignore 데이터를 새 경로로 옮긴다.
rem  git pull 은 추적 파일만 옮기고 gitignore 파일은 옛 자리에 남기므로 필요.
rem
rem  사용(cmd): 브랜치 checkout/pull 후  ->  src\tools\migrate_local_cache.bat
rem  안전: 대상 없으면 skip, 이미 옮겨졌으면 덮어쓰지 않음. 여러 번 실행해도 무해.
rem  이동 대상 아님(경로 그대로라 정상): .env  /  assets\lyrics\
rem =====================================================================

rem 이 스크립트 위치(src\tools\) 기준으로 레포 루트로 이동 -> CWD 무관하게 동작
pushd "%~dp0..\.."
echo [migrate] repo root: %CD%
echo.

rem --- 1) 오디오 캐시 (gitignore, 재다운로드 비쌈): cluster\ -^> src\content\cluster\ ---
if not exist "src\content\cluster\" mkdir "src\content\cluster"
call :move_dir  "cluster\audio_cache"  "src\content\cluster\audio_cache"
call :move_dir  "cluster\audio_full"   "src\content\cluster\audio_full"

rem --- 2) 재생성 가능한 네트워크 캐시: tools\curate\ -^> src\tools\curate\ ---
if not exist "src\tools\curate\" mkdir "src\tools\curate"
call :move_file "tools\curate\verify_cache.json" "src\tools\curate\verify_cache.json"
call :move_file "tools\curate\plb_cache.json"    "src\tools\curate\plb_cache.json"

rem --- 3) 옛 임시/파생물 삭제 (cluster\_* : _ffbin 등, 재생성 가능) ---
if exist "cluster\" (
  for /d %%d in ("cluster\_*") do rmdir /S /Q "%%d" 2>nul
  del /Q "cluster\_*" 2>nul
)

rem --- 4) 옛 __pycache__ (stale 바이트코드) 삭제 ---
if exist "tools\" for /d /r "tools" %%d in (__pycache__) do if exist "%%d" rmdir /S /Q "%%d" 2>nul

rem --- 5) 비어버린 옛 디렉토리 정리 (빈 것만 삭제, 내용 남으면 유지) ---
for %%r in (cluster data wordcloud templates tests tools) do (
  if exist "%%r\" (
    for /f "delims=" %%d in ('dir /ad /b /s "%%r" 2^>nul ^| sort /r') do rmdir "%%d" 2>nul
    rmdir "%%r" 2>nul
    if exist "%%r\" echo [note] "%%r\" 에 파일이 남아 유지함 ^(직접 확인 요망^)
  )
)

echo.
echo [migrate] 완료.
echo   - .env, assets\lyrics\ : 이동 대상 아님 ^(경로 그대로가 정상^)
echo   - 오디오 캐시 위치      : src\content\cluster\
popd
endlocal
goto :eof

rem ---------- 서브루틴 ----------
:move_dir
rem %1 = 원본 디렉토리, %2 = 대상 디렉토리(새 전체 경로)
if not exist "%~1\" ( echo [skip] "%~1" 없음 & goto :eof )
if exist "%~2\"     ( echo [skip] "%~2" 이미 존재 - 유지 & goto :eof )
move "%~1" "%~2" >nul && echo [move] "%~1"  -^>  "%~2"
goto :eof

:move_file
if not exist "%~1" ( echo [skip] "%~1" 없음 & goto :eof )
if exist "%~2"     ( echo [skip] "%~2" 이미 존재 - 유지 & goto :eof )
move "%~1" "%~2" >nul && echo [move] "%~1"  -^>  "%~2"
goto :eof
