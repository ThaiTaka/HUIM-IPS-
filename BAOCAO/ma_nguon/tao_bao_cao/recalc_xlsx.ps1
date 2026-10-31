# Mở sổ Excel bằng COM, tính lại toàn bộ công thức và lưu, để mọi ô có sẵn giá trị khi mở bằng trình xem không tính lại.
# Chạy: powershell -File src/baocao/recalc_xlsx.ps1 <đường dẫn .xlsx>
param([Parameter(Mandatory = $true)][string]$Path)
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
$wb = $xl.Workbooks.Open((Resolve-Path $Path).Path)
$xl.CalculateFull()
$wb.Save()
$wb.Close($false)
$xl.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null
Write-Output "recalc ok: $Path"
