
::CHANGE::
set LAZURIT_DIR={program_path}
set LAZURIT_WORK_DIR={task_dir}
::

::DO NOT CHANGE::
set LIB_PATH=%LAZURIT_DIR%\libraries
set CRT_140=%LIB_PATH%\Microsoft.VC140.CRT
set CRT_120=%LIB_PATH%\Microsoft.VC120.CRT
set intelWIN=%LIB_PATH%\intel64_win
set MPIRT=%LIB_PATH%\intel64_win\mpirt
set Compiler=%LIB_PATH%\intel64_win\compiler
set Compiler_1033=%LIB_PATH%\intel64_win\compiler\1033
set Compiler_1041=%LIB_PATH%\intel64_win\compiler\1041
set Crypto=%LIB_PATH%\Crypto
set TEC17=%LIB_PATH%\tec17
set TEC18=%LIB_PATH%\tec18
set PATH=%LIB_PATH%;%CRT_140%;%CRT_120%;%intelWIN%;%MPIRT%;%Compiler%;%Compiler_1033%;%Compiler_1041%;%Crypto%;%TEC17%;%TEC18%;%LAZURIT_DIR%;%LAZURIT_WORK_DIR%;%PATH%
:: 
::POSSIBLE_KEYS::
:: --import_mesh :: mesh import
:: --dont :: start calc from the beginig
:: --cont -1 :: continue calc 
:: --threads 8 :: Number of OpenMP threads (equal to number of cores on your comuter)
::
{
    swsdsada
}


@echo %date% %time% >time_file.txt

powershell "{program_path}/{comand}"

@echo %date% %time% >>time_file.txt

