# Error License(s. delemiter is ;)
$licenses_to_avoid = "UNKNOWN;"

# Refresh
$result_path = "$PSScriptRoot\result"
Remove-Item $result_path -Recurse -Force > $null
New-Item -Path $result_path -ItemType Directory > $null

# Batch check
$check_result_path = "$PSScriptRoot\result\batch_check_result.txt"
poetry run pip-licenses --format=markdown --fail-on=$licenses_to_avoid > $check_result_path
if ((Get-Item $check_result_path).Length -eq 0) {
    Write-Output "Check failed! Some packages contain $licenses_to_avoid." >> $check_result_path
} else {
    Write-Output "Check succeed! Please re-check the summary files too." >> $check_result_path
}

# Summary to check manually
poetry run pip-licenses --format=markdown > $PSScriptRoot\result\_OSS-LICENSES-Summary.md
poetry run pip-licenses --format=csv --with-urls > $PSScriptRoot\result\_OSS-LICENSES-Summary.csv

# OSS-LICENSES.txt
poetry run pip-licenses --format=plain-vertical --no-license-path --with-license-file > $PSScriptRoot\result\OSS-LICENSES.txt
