@echo off
setlocal
cd /d "%~dp0"
if not exist out mkdir out
javac --release 17 -encoding UTF-8 -d out java\*.java
if errorlevel 1 exit /b 1
java -cp out ReservationTests
if errorlevel 1 exit /b 1
java -cp out PetriExplorer modeles/reservation.pnml
if errorlevel 1 exit /b 1
java -cp out PetriExplorer modeles/reservation-pipe.xml
if errorlevel 1 exit /b 1
java -cp out PetriExplorer modeles/reservation-incorrecte.pnml --expect-unsafe
if errorlevel 1 exit /b 1
java -cp out ProbabilityAnalysis
if errorlevel 1 exit /b 1
echo Verification Java terminee.
