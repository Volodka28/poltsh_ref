#!MC 1410
$!ReadDataSet  '$input_files$'
  ReadDataOption = New
  ResetStyle = Yes
  VarLoadMode = ByName
  AssignStrandIDs = Yes

$!AlterData 
  Equation = '{angle}=ATAN({Y}/{X})*180/3.14159'
$!AlterData 
  Equation = '{Nu_inf}={alpha}*0.05/(1006.43*0.000017204/0.72)'
$!AlterData 
  Equation = '{c_f}={tau_w}/5975.61'
$!AlterData 
  Equation = '{c_p}=({p}-$Boundary Conditions.Inlet.Static Pressure, Pa$)/5975.61'
$!WriteDataSet  "$output_path$\Nu.dat"
  IncludeText = No
  IncludeGeom = No
  IncludeDataShareLinkage = Yes
  ZoneList =  [13-18]  
  VarPositionList =  [1,2,4,30,29,36-38,51-54]
  Binary = No
  UsePointFormat = Yes
  Precision = 9
  TecplotVersionToWrite = TecplotCurrent
