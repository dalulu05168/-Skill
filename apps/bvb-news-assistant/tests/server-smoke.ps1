$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$exe=(Get-Process -Id $PID).Path
$proc=$null
try {
 $server=Join-Path $root 'BVB_Server.ps1'
 $proc=Start-Process -FilePath $exe -ArgumentList @('-NoLogo','-NoProfile','-File',('"'+$server+'"'),'-NoBrowser','-Port','19011') -PassThru
 $base='http://127.0.0.1:19011'
 $ready=$false
 for($i=0;$i -lt 40;$i++){
  try{$status=Invoke-RestMethod "$base/api/status" -TimeoutSec 2;if($status.ok -and $status.version -eq '5.0'){$ready=$true;break}}catch{}
  Start-Sleep -Milliseconds 250
 }
 if(-not $ready){throw 'Server failed to start on test port'}
 $page=Invoke-WebRequest "$base/" -UseBasicParsing -TimeoutSec 5
 if($page.StatusCode -ne 200 -or $page.Content -notmatch 'collection-core.js'){throw 'UI entry unavailable'}
 $script=Invoke-WebRequest "$base/collection-core.js" -UseBasicParsing -TimeoutSec 5
 if($script.Content -notmatch 'BVB_COLLECTION'){throw 'Core module unavailable'}
 $bad=Invoke-RestMethod "$base/api/market?key=INVALID" -TimeoutSec 5
 if($bad.state -ne 'unavailable'){throw 'Invalid market key not rejected'}
 $rejected=$false
 try{Invoke-WebRequest "$base/api/article?url=https%3A%2F%2F127.0.0.1%2Fsecret" -UseBasicParsing -TimeoutSec 5 | Out-Null}catch{if([int]$_.Exception.Response.StatusCode -eq 400){$rejected=$true}}
 if(-not $rejected){throw 'Unsafe article URL was not blocked'}
 Write-Output 'PASS real server startup, HTTP status, page/core routes, invalid keys and unsafe URL rejection'
}finally{if($proc -and -not $proc.HasExited){Stop-Process -Id $proc.Id -Force}}
