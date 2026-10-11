$ErrorActionPreference='Stop'
$server=Join-Path (Split-Path $PSScriptRoot -Parent) 'BVB_Server.ps1'
$errors=$null;$tokens=$null
[System.Management.Automation.Language.Parser]::ParseFile($server,[ref]$tokens,[ref]$errors)>$null
if($errors.Count){throw ($errors|Out-String)}
. $server -LibraryOnly
foreach($url in @('http://www.bvb.ro/','https://127.0.0.1/','https://www.bvb.ro.evil.test/','https://user@www.bvb.ro/')){if(Article-Allowed $url){throw "Unsafe URL accepted: $url"}}
if(-not (Article-Allowed 'https://www.economica.net/feed')){throw 'New source not allowed'}
$page='<a href="/stiri/politic/test-economic-headline-123456">Public economic article headline with enough text</a><a href="https://evil.test/news/articles/test">A malicious external URL with long title</a>'
$f=$feeds|Where-Object id -eq 'profit-politic'
$rows=@(Extract-PageCandidates $page $f)
if($rows.Count -ne 1 -or $rows[0].dateRaw -ne ''){throw 'Page parse provenance incorrect'}
# Fixture responses are deliberately isolated; this is not a live market claim.
function Fetch-Url($url){
 if($url -match 'finance/chart'){
  return '{"chart":{"result":[{"meta":{"regularMarketPrice":5.25,"regularMarketTime":1791838800,"currency":"USD","exchangeTimezoneName":"America/New_York","previousClose":4.9},"timestamp":[1791583200,1791838800],"indicators":{"quote":[{"close":[5.2,5.25]}]}}],"error":null}}'
 }
 if($url -match 'bloomberg|reuters|cn.wsj|stiri/politic'){return '<a href="/news/articles/test-story">A public headline for the isolated fixture check</a>'}
 if($url -match 'Intraday'){throw 'Fixture: quote unavailable'}
 return '<rss version="2.0"><channel><item><title>Fixture financial news title</title><link>https://www.bursa.ro/fixture</link><pubDate>Mon, 12 Oct 2026 05:00:00 GMT</pubDate><description>Fixture, not actual news</description></item></channel></rss>'
}
$m=Fetch-MarketMetric 'TTF'
if($null -ne $m.value -or $null -ne $m.change_pct -or $null -ne $m.baseline -or $null -ne $m.previous_session_close){throw 'Missing TTF retained numeric dependent fields'}
$m=Fetch-MarketMetric 'US10Y'
if([Math]::Abs($m.change_basis_points-5) -gt 0.00001){throw 'Yield basis points incorrect'}
if($m.baseline -ne 5.2){throw 'Prior daily close not selected'}
$ids=@($feeds.id)
foreach($id in @('bursa','economica','profit-politic','profit','romania-insider','bloomberg','reuters','wsj-cn')){if($id -notin $ids){throw "Source missing: $id"}}
if('eurostat' -in $ids){throw 'Cancelled source restored'}
Write-Output 'PASS server: syntax, source configuration, page provenance, safe URLs, TTF dependencies, US10Y basis points'
