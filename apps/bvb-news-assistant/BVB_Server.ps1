# BVB News Desk v4 Chinese | Windows PowerShell 5.1+ | No additional packages
param([int]$Port=18986,[switch]$NoBrowser,[switch]$LibraryOnly)
$script:translationCache=@{}
$ErrorActionPreference='Stop'
# Suppress parser DTD resolution and keep publication timestamps distinct from fetch time.
$ProgressPreference='SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$root=Split-Path -Parent $MyInvocation.MyCommand.Path
$feeds=@(
 @{id='bvb-market';name='BVB 官方市场公告';tier='official';url='https://www.bvb.ro/Rss/StiriBVB.ashx';alternatives=@('https://bvb.ro/Rss/StiriBVB.ashx')},
 @{id='bvb-issuer';name='BVB 公司财务披露';tier='official';url='https://www.bvb.ro/Rss2/LastFinancialData.ashx?lang=ro';alternatives=@('https://www.bvb.ro/Rss2/LastFinancialData.ashx')},
 @{id='bvb-operation';name='BVB 交易所公告';tier='official';url='https://www.bvb.ro/Rss/OperatiuniSiComunicateBVB.ashx';alternatives=@('https://bvb.ro/Rss/OperatiuniSiComunicateBVB.ashx')},
 @{id='fed';name='美联储新闻公告';tier='official';url='https://www.federalreserve.gov/feeds/press_all.xml'},
 @{id='bls';name='美国劳工统计局发布';tier='official';url='https://www.bls.gov/feed/bls_latest.rss'},
 @{id='ecb';name='欧洲央行公告';tier='official';url='https://www.ecb.europa.eu/rss/press.html'},
 @{id='economica';name='Economica';tier='media';url='https://www.economica.net/feed'},
 @{id='profit-politic';name='Profit 指定栏目（仅经济事实候审）';tier='media';url='https://www.profit.ro/stiri/politic/';kind='page'},
 @{id='profit';name='Profit 新闻RSS（政治栏目需经济事实筛选）';tier='media';url='https://www.profit.ro/rss'},
 @{id='romania-insider';name='Romania Insider Business';tier='media';url='https://www.romania-insider.com/business/feed.xml';alternatives=@('https://www.romania-insider.com/feed.xml')},
 @{id='bloomberg';name='Bloomberg Asia';tier='media';url='https://www.bloomberg.com/asia';kind='page'},
 @{id='reuters';name='Reuters';tier='media';url='https://www.reuters.com/';kind='page'},
 @{id='wsj-cn';name='华尔街日报中文网';tier='media';url='https://cn.wsj.com/';kind='page'},
 @{id='bursa';name='BURSA 资本市场资讯';tier='media';url='https://www.bursa.ro/_rss/?t=pcaps';alternatives=@('https://www.bursa.ro/piata-capital-bursa.xml')}
)
$priorityIds=@('bursa','economica','profit-politic','profit','romania-insider','bloomberg','reuters','wsj-cn')
$feeds=@($feeds | Sort-Object @{Expression={ $rank=[array]::IndexOf($priorityIds,$_.id);if($rank -lt 0){100}else{$rank}}})
function Text-Node($node, $localName) {
 $child=$node.SelectSingleNode('./*[local-name()="'+$localName+'"]')
 if($null -eq $child){return ''}
 if($localName -eq 'link' -and $child.Attributes -and $child.Attributes['href']){return [string]$child.Attributes['href'].Value}
 return [string]$child.InnerText
}
function Clean-Text($value) {
 if(-not $value){return ''}
 $v=[Net.WebUtility]::HtmlDecode([string]$value)
 $v=[regex]::Replace($v,'<[^>]*>',' ')
 $v=[regex]::Replace($v,'\s+',' ').Trim()
 if($v.Length -gt 300){$v=$v.Substring(0,300)+'…'}
 return $v
}
# Decode the original network BYTES rather than Invoke-WebRequest.Content.
# Windows PowerShell 5.1 can otherwise interpret Romanian UTF-8 with a wrong charset.
function Decode-FeedBytes([byte[]]$bytes,[string]$headerType) {
 if($null -eq $bytes -or $bytes.Length -eq 0){throw '空响应'}
 $offset=0
 $label='utf-8'
 if($bytes.Length -ge 3 -and $bytes[0] -eq 239 -and $bytes[1] -eq 187 -and $bytes[2] -eq 191){
  $offset=3
  $label='utf-8'
 }elseif($bytes.Length -ge 2 -and $bytes[0] -eq 255 -and $bytes[1] -eq 254){
  $offset=2
  $label='utf-16'
 }elseif($bytes.Length -ge 2 -and $bytes[0] -eq 254 -and $bytes[1] -eq 255){
  $offset=2
  $label='utf-16BE'
 }else{
  $prefix=[Text.Encoding]::ASCII.GetString($bytes,0,[Math]::Min(1200,$bytes.Length))
  # XML declaration takes precedence over HTTP headers in XML reader rules.
  if($prefix -match '(?is)^\s*<\?xml[^>]+encoding\s*=\s*["'']([^"''\s>]+)'){
   $label=$matches[1].Trim()
  }elseif($prefix -match '(?is)<meta[^>]+charset\s*=\s*["'']?([a-zA-Z0-9._-]+)'){
   $label=$matches[1].Trim()
  }elseif($headerType -match '(?i)charset\s*=\s*["'']?([a-zA-Z0-9._-]+)'){
   $label=$matches[1].Trim()
  }
 }
 try{
  if($label -match '^(?i:utf-8|utf8)$'){
   $encoder=[System.Text.UTF8Encoding]::new($false,$true)
  }else{
   $encoder=[Text.Encoding]::GetEncoding($label,[Text.EncoderFallback]::ExceptionFallback,[Text.DecoderFallback]::ExceptionFallback)
  }
  $result=$encoder.GetString($bytes,$offset,$bytes.Length-$offset)
  if([string]::IsNullOrWhiteSpace($result)){throw '解码后内容为空'}
  return $result
 }catch{
  throw ('字符集解码失败（'+$label+'）：'+$_.Exception.Message)
 }
}
# Download actual response bytes and decode from BOM / XML declaration; do not trust
# PowerShell 5.1 Invoke-WebRequest.Content's automatic text charset inference.
function Fetch-Url($url) {
 if(-not (Article-Allowed $url)){throw 'RSS网址不在允许的HTTPS来源域名内'}
 $current=[string]$url
 for($redirect=0;$redirect -le 3;$redirect++){
  if(-not (Article-Allowed $current)){throw '来源重定向到未允许的域名，已拒绝访问'}
  $req=[System.Net.HttpWebRequest][Net.WebRequest]::Create($current)
  $req.Method='GET';$req.Timeout=6500;$req.ReadWriteTimeout=6500
  $req.AllowAutoRedirect=$false
  $req.UserAgent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) BVBNewsAssistant/5.0'
  $req.Accept='application/rss+xml,application/atom+xml,application/xml,text/xml,text/html;q=0.8,*/*;q=0.3'
  $req.AutomaticDecompression=[Net.DecompressionMethods]::GZip -bor [Net.DecompressionMethods]::Deflate
  $res=$null
  try {
   $res=[System.Net.HttpWebResponse]$req.GetResponse()
   $status=[int]$res.StatusCode
   if($status -in @(301,302,303,307,308)){
    $location=$res.Headers['Location']
    if(-not $location){throw 'RSS返回重定向但没有Location'}
    $target=[Uri]::new([Uri]$current,$location).AbsoluteUri
    if(-not (Article-Allowed $target)){throw 'RSS重定向目标不是受支持的HTTPS来源'}
    $current=$target;continue
   }
   if($status -ne 200){throw ('RSS服务器返回HTTP '+$status)}
   if($res.ContentLength -gt 3000000){throw 'RSS超过3MB大小限制'}
   $stream=$res.GetResponseStream()
   if($null -eq $stream){throw '新闻源没有返回可读取数据流'}
   $mem=New-Object IO.MemoryStream
   try {
    $buf=New-Object byte[] 8192
    while(($n=$stream.Read($buf,0,$buf.Length)) -gt 0){
     $mem.Write($buf,0,$n)
     if($mem.Length -gt 3000000){throw 'RSS超过3MB大小限制'}
    }
    $bytes=$mem.ToArray()
   }finally{$mem.Dispose();$stream.Dispose()}
   return Decode-FeedBytes $bytes ([string]$res.ContentType)
  }catch [Net.WebException] {
   $http=$_.Exception.Response
   if($http -is [Net.HttpWebResponse]){throw ('HTTP '+[int]$http.StatusCode+' '+$http.StatusDescription+'，'+$_.Exception.Message)}
   throw ('连接失败：'+$_.Exception.Message)
  }finally{if($null -ne $res){$res.Dispose()}}
 }
 throw '新闻源连续重定向超过3次'
}
function Article-Allowed($raw) {
 if(-not $raw -or ([string]$raw).Length -gt 2000){return $false}
 $uri=$null
 if(-not [Uri]::TryCreate([string]$raw,[UriKind]::Absolute,[ref]$uri)){return $false}
 if($uri.Scheme -ne 'https' -or $uri.UserInfo -or $uri.Port -ne 443){return $false}
 return ($uri.Host -match '(^|\.)(bvb\.ro|ecb\.europa\.eu|bursa\.ro|economica\.net|profit\.ro|romania-insider\.com|bloomberg\.com|reuters\.com|wsj\.com|federalreserve\.gov|bls\.gov|ec\.europa\.eu|query1\.finance\.yahoo\.com|finance\.yahoo\.com)$')
}
function Fetch-Article($url) {
 if(-not (Article-Allowed $url)){throw '仅允许打开已授权新闻源的HTTPS网页'}
 $response=Fetch-Url $url
 if($response -match '(?is)<article\b[^>]*>(.*?)</article>'){$body=$matches[1]}else{$body=$response}
 $body=[regex]::Replace($body,'(?is)<(script|style|nav|header|footer|noscript|svg|form|aside)\b[^>]*>.*?</\1>',' ')
 $body=[regex]::Replace($body,'(?is)<(p|h1|h2|h3|li|br|div|section)\b[^>]*>',"`n")
 $body=[regex]::Replace($body,'(?is)<[^>]+>',' ')
 $body=[Net.WebUtility]::HtmlDecode($body)
 $body=[regex]::Replace($body,'[ \t]+',' ')
 $body=[regex]::Replace($body,'(?:\r?\n[ \t]*){3,}',"`n`n").Trim()
 if($body.Length -gt 12000){$body=$body.Substring(0,12000)+'…（内容已截断，请以原文为准）'}
 if($body.Length -lt 90){throw '网页可提取正文过短，可能为动态页面、PDF或访问受限；请打开原始网页核对'}
 return @{url=$url;fetchedAt=[DateTimeOffset]::UtcNow.ToString('o');content=$body;length=$body.Length;verified=$false;warning='仅为机器提取的网页文字，不能代替原文及人工事实核验'}
}

# Public delayed reference quotes. Failures are missing data, never fabricated values.
$marketSpecs=@{
 'SP500'=@{symbol='^GSPC';name='S&P500';unit='points';group='international'}
 'NASDAQ'=@{symbol='^IXIC';name='Nasdaq Composite';unit='points';group='international'}
 'DAX'=@{symbol='^GDAXI';name='DAX';unit='points';group='international'}
 'FTSE'=@{symbol='^FTSE';name='FTSE100';unit='points';group='international'}
 'BRENT'=@{symbol='BZ=F';name='Brent futures';unit='USD/barrel';group='energy'}
 'TTF'=@{symbol='TTF=F';name='TTF futures (provider symbol must be verified)';unit='provider';group='energy'}
 'SP_FUTURE'=@{symbol='ES=F';name='S&P500 futures';unit='points';group='international'}
 'NQ_FUTURE'=@{symbol='NQ=F';name='Nasdaq100 futures';unit='points';group='international'}
 'US10Y'=@{symbol='^TNX';name='US10Y reference yield index';unit='percent';group='international'}
 'DXY'=@{symbol='DX-Y.NYB';name='DXY';unit='index';group='international'}
 'USDRON'=@{symbol='RON=X';name='USD/RON';unit='RON/USD';group='international'}
 'EURRON'=@{symbol='EURRON=X';name='EUR/RON';unit='RON/EUR';group='international'}
}
function Fetch-MarketMetric($key) {
 if(-not $marketSpecs.ContainsKey($key)){throw 'Unknown market key'}
 $spec=$marketSpecs[$key]
 $url='https://query1.finance.yahoo.com/v8/finance/chart/'+[Uri]::EscapeDataString($spec.symbol)+'?interval=1d&range=10d'
 $result=(Fetch-Url $url)|ConvertFrom-Json
 if($result.chart.error -or -not $result.chart.result){throw 'Provider did not return a chart'}
 $chart=$result.chart.result[0];$meta=$chart.meta
 if($null -eq $meta.regularMarketPrice -or $null -eq $meta.regularMarketTime){throw 'Missing quote or observation timestamp'}
 $value=[double]$meta.regularMarketPrice
 if([double]::IsNaN($value) -or [double]::IsInfinity($value)){throw 'Invalid quote value'}
 $observed=[DateTimeOffset]::FromUnixTimeSeconds([long]$meta.regularMarketTime).ToString('o')
 $metric=@{id=('auto-'+$key);group=$spec.group;name=$spec.name;asset=$key;provider_symbol=$spec.symbol;value=$value;unit=$spec.unit;observed_at=$observed;collected_at=[DateTimeOffset]::UtcNow.ToString('o');source_url=$url;verification_status='UNVERIFIED';verification_note='';period='PROVIDER_QUOTE';currency=$meta.currency;contract_note='Provider continuous/nearby reference; contract month not guaranteed';baseline=$null;change_pct=$null;previous_session_close=$null;previous_session_at=$null;warning='Public provider reference, may be delayed; not official exchange confirmation'}
 # Keep prior daily bars separately from the latest potentially partial bar.
 $closes=$chart.indicators.quote[0].close;$times=$chart.timestamp
 $latestDate=[DateTimeOffset]::FromUnixTimeSeconds([long]$meta.regularMarketTime).UtcDateTime.Date
 for($i=$times.Count-1;$i -ge 0;$i--){
  if($null -eq $closes[$i]){continue}
  $barDate=[DateTimeOffset]::FromUnixTimeSeconds([long]$times[$i]).UtcDateTime.Date
  if($barDate -lt $latestDate){$metric.previous_session_close=[double]$closes[$i];$metric.previous_session_at=[DateTimeOffset]::FromUnixTimeSeconds([long]$times[$i]).ToString('o');break}
 }
 if($null -ne $metric.previous_session_close){$metric.baseline=$metric.previous_session_close}
 elseif($null -ne $meta.previousClose){$metric.baseline=[double]$meta.previousClose}
 if($null -ne $metric.baseline -and $metric.baseline -gt 0){$metric.change_pct=100*($value-$metric.baseline)/$metric.baseline}
 $metric.exchange_timezone=$meta.exchangeTimezoneName
 $metric.baseline_kind='PRIOR_DAILY_BAR_OR_PROVIDER_PREVIOUS_CLOSE'
 $metric.change_basis_points=$null
 if($key -eq 'US10Y' -and $null -ne $metric.baseline){$metric.change_basis_points=100*($value-$metric.baseline)}
 # The ticker alone is insufficient to certify the TTF product/contract/unit.
 if($key -eq 'TTF'){$metric.value=$null;$metric.change_pct=$null;$metric.baseline=$null;$metric.previous_session_close=$null;$metric.previous_session_at=$null;$metric.verification_status='MISSING';$metric.warning='TTF contract identity/unit require verified data source; returned price withheld'}
 return $metric
}

function Extract-PageCandidates($content,$feed) {
 $out=New-Object 'System.Collections.Generic.List[object]'
 $seen=New-Object 'System.Collections.Generic.HashSet[string]'
 $base=[Uri]$feed.url
 foreach($m in [regex]::Matches($content,'(?is)<a\b[^>]*href=["'']([^"'']+)["''][^>]*>(.*?)</a>')) {
  $title=Clean-Text $m.Groups[2].Value
  if($title.Length -lt 24 -or $title.Length -gt 350){continue}
  try{$uri=[Uri]::new($base,[Net.WebUtility]::HtmlDecode($m.Groups[1].Value))}catch{continue}
  if(-not (Article-Allowed $uri.AbsoluteUri) -or $uri.Host -ne $base.Host){continue}
  if($uri.AbsolutePath -notmatch '(?:/news/articles/|/business/.+|/world/.+|/articles/.+|/stiri/politic/.+-[0-9]{5,}|/zh-hans/.+)'){continue}
  $url=$uri.GetLeftPart([UriPartial]::Path)
  if(-not $seen.Add($url)){continue}
  $out.Add(@{title=$title;url=$url;description='公开栏目页面标题；未读取全文，发布时间未知';guid=$url;dateRaw='';sourceId=$feed.id;source=$feed.name;tier=$feed.tier;sourceUrl=$feed.url})
  if($out.Count -ge 40){break}
 }
 return $out.ToArray()
}

function Fetch-Feeds {
 $all=New-Object 'System.Collections.Generic.List[object]'
 $states=New-Object 'System.Collections.Generic.List[object]'
 foreach($feed in $feeds){
  $failures=New-Object 'System.Collections.Generic.List[string]'
  $worked=$false
  $candidateUrls=@($feed.url)+@($feed.alternatives)
  foreach($candidate in $candidateUrls){
   if(-not $candidate){continue}
   try {
    $content=Fetch-Url $candidate
    if($feed.kind -eq 'page'){
     $rows=@(Extract-PageCandidates $content $feed)
     if($rows.Count -eq 0){throw '页面可访问，但未提取到可追溯新闻标题；可能为访问限制或页面改版'}
     foreach($row in $rows){$all.Add($row)}
     $states.Add(@{id=$feed.id;name=$feed.name;url=$candidate;state='ok';attemptedAt=[DateTimeOffset]::UtcNow.ToString('o');count=$rows.Count;message='仅公开栏目标题，发布时间未知，非全文核验';attempts=$failures.Count+1})
     $worked=$true;break
    }
    if($content -notmatch '(?is)<(rss|feed|rdf:RDF|\?xml)\b'){throw '返回HTML或非RSS内容，未发现XML/RSS标记'}
    $xml=New-Object System.Xml.XmlDocument
    $xml.XmlResolver=$null
    $settings=New-Object System.Xml.XmlReaderSettings;$settings.DtdProcessing=[System.Xml.DtdProcessing]::Prohibit;$settings.XmlResolver=$null;$reader=[System.Xml.XmlReader]::Create((New-Object IO.StringReader($content)),$settings);try{$xml.Load($reader)}finally{$reader.Dispose()}
    $nodes=$xml.SelectNodes('//*[local-name()="item" or local-name()="entry"]')
    if($null -eq $nodes -or $nodes.Count -eq 0){throw '页面可访问但没有RSS/Atom文章条目'}
    $count=0
   foreach($node in $nodes){
    if($count -ge 100){break}
    $title=Clean-Text (Text-Node $node 'title')
    $link=(Text-Node $node 'link').Trim()
    if(-not $link -or -not $title){continue}
    $uri=$null
    if(-not [Uri]::TryCreate($link,[UriKind]::Absolute,[ref]$uri)){continue}
    if($uri.Scheme -ne 'https' -and $uri.Scheme -ne 'http'){continue}
    $desc=Clean-Text (Text-Node $node 'description')
    if(-not $desc){$desc=Clean-Text (Text-Node $node 'summary')}
    if(-not $desc){$desc=Clean-Text (Text-Node $node 'content')}
    $guid=Text-Node $node 'guid'
    if(-not $guid){$guid=Text-Node $node 'id'}
    $dt=(Text-Node $node 'pubDate')
    if(-not $dt){$dt=Text-Node $node 'published'}
    if(-not $dt){$dt=Text-Node $node 'updated'}
    $all.Add(@{title=$title;url=$link;description=$desc;guid=$guid;dateRaw=$dt;sourceId=$feed.id;source=$feed.name;tier=$feed.tier;sourceUrl=$candidate})
    $count++
   }
    if($count -eq 0){throw 'RSS没有有效标题与链接，不能标记采集成功'}
    $states.Add(@{id=$feed.id;name=$feed.name;url=$candidate;state='ok';attemptedAt=[DateTimeOffset]::UtcNow.ToString('o');count=$count;message=('本次成功'+$count+'条；使用：'+$candidate);attempts=$failures.Count+1})
    $worked=$true;break
   }catch{
    $msg=[string]$_.Exception.Message
    if($msg.Length -gt 155){$msg=$msg.Substring(0,155)}
    $failures.Add(($candidate+': '+$msg))
   }
  }
  if(-not $worked){
   $message=$failures -join ' | '
   if($message.Length -gt 360){$message=$message.Substring(0,360)+'…'}
   $states.Add(@{id=$feed.id;name=$feed.name;url=$feed.url;state='failed';attemptedAt=[DateTimeOffset]::UtcNow.ToString('o');count=0;message=$message;attempts=$failures.Count})
  }
 }
 $quote=@{state='unavailable';source='BVB WebDelayed';url='https://ws.bvb.ro/BVBDelayedWS/Intraday.asmx?op=GetIndex';manualUrl='https://www.bvb.ro/TradingAndStatistics/Trading/MarketsToday';note='官方数据接口未返回合格BET报价；请进入BVB官方行情页面人工核实';value=$null;change=$null;marketTime=$null;method=$null}
 $errors=@()
 foreach($method in @('GET','SOAP')){
  try {
   if($method -eq 'GET'){
    $content=Fetch-Url 'https://ws.bvb.ro/BVBDelayedWS/Intraday.asmx/GetIndex?code=BET'
   }else{
    $soap=@'
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><GetIndex xmlns="www.bvb.ro"><code>BET</code></GetIndex></soap:Body></soap:Envelope>
'@
    $headers=@{'SOAPAction'='"www.bvb.ro/GetIndex"';'User-Agent'='BVBNewsAssistant/5.0'}
    $res=Invoke-WebRequest -Uri 'https://ws.bvb.ro/BVBDelayedWS/Intraday.asmx' -Method Post -UseBasicParsing -Headers $headers -ContentType 'text/xml; charset=utf-8' -Body $soap -TimeoutSec 8 -MaximumRedirection 0 -ErrorAction Stop
    $content=[string]$res.Content
   }
   $xml=New-Object System.Xml.XmlDocument
   $xml.XmlResolver=$null
   $settings=New-Object System.Xml.XmlReaderSettings;$settings.DtdProcessing=[System.Xml.DtdProcessing]::Prohibit;$settings.XmlResolver=$null;$reader=[System.Xml.XmlReader]::Create((New-Object IO.StringReader($content)),$settings);try{$xml.Load($reader)}finally{$reader.Dispose()}
   $node=$xml.SelectSingleNode('//*[local-name()="TypeIndices" and *[local-name()="Code" and normalize-space(.)="BET"]]')
   if($null -eq $node){throw '响应没有BET指数记录（可能需要数据访问权限）'}
   $value=Text-Node $node 'CurrentValue';$change=Text-Node $node 'PrcChange';$marketTime=Text-Node $node 'LastUpdateTime'
   $valueFloat=0.0;$changeFloat=0.0
   if(-not [double]::TryParse($value,[Globalization.NumberStyles]::Float,[Globalization.CultureInfo]::InvariantCulture,[ref]$valueFloat)){throw '指数数值解析失败'}
   if(-not [double]::TryParse($change,[Globalization.NumberStyles]::Float,[Globalization.CultureInfo]::InvariantCulture,[ref]$changeFloat)){throw '涨跌幅解析失败'}
   if($valueFloat -le 0 -or $valueFloat -gt 1000000 -or [math]::Abs($changeFloat) -gt 90){throw '数值超出可接受范围'}
   if([string]::IsNullOrWhiteSpace($marketTime)){throw '未返回行情观测时间，禁止当成当前价格'}
   $quote=@{state='ok';source='BVB WebDelayed';url='https://ws.bvb.ro/BVBDelayedWS/Intraday.asmx?op=GetIndex';manualUrl='https://www.bvb.ro/TradingAndStatistics/Trading/MarketsToday';note='官方接口返回报价，发布前仍需核对数据日期与延迟/授权';value=$valueFloat;change=$changeFloat;marketTime=$marketTime;method=$method}
   break
  }catch {
   $message=[string]$_.Exception.Message
   if($message.Length -gt 130){$message=$message.Substring(0,130)}
   $errors+=($method+': '+$message)
  }
 }
 if($quote.state -ne 'ok'){$quote.note='自动报价不可用（GET及SOAP均未取得有效响应）：'+($errors -join '；')+'。可打开BVB官方行情页面人工确认。'}
 return @{fetchedAt=[DateTimeOffset]::UtcNow.ToString('o');articles=@($all.ToArray());sources=@($states.ToArray());quote=$quote;live=$true}
}

# Optional public-headline machine translation. Public article title is sent to MyMemory,
# not to BVB. Output is never treated as verified financial facts.
function Translate-Headline([string]$raw,[string]$sourceLang){
 if([string]::IsNullOrWhiteSpace($raw) -or $raw.Length -gt 320){throw '标题为空或超过翻译长度上限'}
 if($sourceLang -notin @('ro','en')){throw '只支持罗马尼亚语或英语新闻标题'}
 $key=$sourceLang+'|'+$raw.Trim()
 if($script:translationCache.ContainsKey($key)){
  $t=$script:translationCache[$key]
  return @{status='ok';translated=$t;provider='MyMemory';cached=$true;verified=$false}
 }
 $query=[Uri]::EscapeDataString($raw.Trim())
 if([Text.Encoding]::UTF8.GetByteCount($raw.Trim()) -gt 450){throw '标题编码超过公开翻译接口的500字节限制'}
 $langpair=[Uri]::EscapeDataString($sourceLang+'|zh-CN')
 $uri='https://api.mymemory.translated.net/get?q='+$query+'&langpair='+$langpair
 $req=[System.Net.HttpWebRequest][Net.WebRequest]::Create($uri)
 $req.Method='GET';$req.Timeout=8500;$req.ReadWriteTimeout=8500;$req.AllowAutoRedirect=$false
 $req.UserAgent='BVBNewsDesk/3.3 public headline translation'
 $res=$null
 try {
  $res=[Net.HttpWebResponse]$req.GetResponse()
  if([int]$res.StatusCode -ne 200){throw ('翻译接口HTTP '+[int]$res.StatusCode)}
  $stream=$res.GetResponseStream();$mem=New-Object IO.MemoryStream
  try{
   $buf=New-Object byte[] 4096
   while(($n=$stream.Read($buf,0,$buf.Length)) -gt 0){$mem.Write($buf,0,$n);if($mem.Length -gt 100000){throw '翻译响应过大'}}
   $payload=[Text.Encoding]::UTF8.GetString($mem.ToArray())
  }finally{$mem.Dispose();$stream.Dispose()}
  $obj=ConvertFrom-Json -InputObject $payload -ErrorAction Stop
  if($null -eq $obj -or [int]$obj.responseStatus -ne 200){throw ('翻译供应商未接受请求：'+[string]$obj.responseDetails)}
  $translation=[Net.WebUtility]::HtmlDecode([string]$obj.responseData.translatedText).Trim()
  if($translation.Length -lt 2 -or $translation -notmatch '[\u4e00-\u9fff]' -or $translation -match 'MYMEMORY WARNING|QUERY LENGTH LIMIT'){throw '服务未返回可用的中文翻译'}
  if($script:translationCache.Count -gt 150){$script:translationCache.Clear()}
  $script:translationCache[$key]=$translation
  return @{status='ok';translated=$translation;provider='MyMemory';cached=$false;verified=$false}
 }catch [Net.WebException]{throw ('在线机翻无法访问：'+$_.Exception.Message)}
 finally{if($null -ne $res){$res.Dispose()}}
}

function Respond($ctx,[int]$status,[string]$body,[string]$type){
 $response=$ctx.Response
 $response.StatusCode=$status
 $response.ContentType=$type+'; charset=utf-8'
 $response.Headers.Add('Cache-Control','no-store, max-age=0')
 $response.Headers.Add('X-Content-Type-Options','nosniff')
 $response.Headers.Add('X-Frame-Options','DENY')
 $b=[Text.Encoding]::UTF8.GetBytes($body)
 $response.ContentLength64=$b.Length
 $response.OutputStream.Write($b,0,$b.Length)
 $response.Close()
}
if($LibraryOnly){return}
$listener=New-Object Net.HttpListener
$running=$false
foreach($portTry in @($Port,18987,18988,18989)){
 try {
  $listener.Prefixes.Clear()
  $listener.Prefixes.Add('http://127.0.0.1:'+($portTry)+'/')
  $listener.Start()
  $Port=$portTry
  $running=$true
  break
 }catch { Write-Host ('端口 '+$portTry+' 无法启动：'+$_.Exception.Message) }
}
if(-not $running){Write-Host '无法启动本地服务。请尝试管理员运行或确认端口没有被占用。';Read-Host '按 Enter 退出';exit 2}
$address='http://127.0.0.1:'+$Port+'/'
Write-Host ''
Write-Host '==================================================' -ForegroundColor DarkYellow
Write-Host 'BVB 资讯台 v5.0 | 新闻源及中文机翻增强版' -ForegroundColor Green
Write-Host ('地址：'+$address)
Write-Host '首次进入网页后点击「立即采集」。' -ForegroundColor Cyan
Write-Host '保留此窗口运行，新闻采集需要互联网连接。'
Write-Host '按 Ctrl+C 可停止服务。'
Write-Host '==================================================' -ForegroundColor DarkYellow
try{if(-not $NoBrowser){Start-Process $address}}catch{Write-Host ('请手动打开：'+$address)}
try{
 while($listener.IsListening){
  $ctx=$listener.GetContext()
  try{
   if($ctx.Request.HttpMethod -ne 'GET'){Respond $ctx 405 '不支持的请求' 'text/plain';continue}
   $path=$ctx.Request.Url.AbsolutePath
   if($path -eq '/api/status'){
    Respond $ctx 200 ('{"ok":true,"version":"5.0","server":"PowerShell","time":"'+[DateTimeOffset]::UtcNow.ToString('o')+'"}') 'application/json';continue
   }
   if($path -eq '/api/market'){
    try{
     $metric=Fetch-MarketMetric ($ctx.Request.QueryString['key'])
     Respond $ctx 200 (ConvertTo-Json -InputObject @{metric=$metric} -Depth 8 -Compress) 'application/json'
    }catch{
     Respond $ctx 200 (ConvertTo-Json -InputObject @{state='unavailable';error=[string]$_.Exception.Message;fetchedAt=[DateTimeOffset]::UtcNow.ToString('o')} -Compress) 'application/json'
    }
    continue
   }
   if($path -eq '/api/translate'){
    try {
     $raw=$ctx.Request.QueryString['text']
     $lang=$ctx.Request.QueryString['lang']
     $result=Translate-Headline $raw $lang
     Respond $ctx 200 (ConvertTo-Json -InputObject $result -Compress -Depth 4) 'application/json'
    }catch{
     $msg=[string]$_.Exception.Message
     Respond $ctx 200 (ConvertTo-Json -InputObject @{status='unavailable';translated=$null;verified=$false;error=$msg} -Compress) 'application/json'
    }
    continue
   }
   if($path -eq '/api/article'){
    try{
     $raw=$ctx.Request.QueryString['url']
     $article=Fetch-Article $raw
     Respond $ctx 200 (ConvertTo-Json -InputObject $article -Depth 5 -Compress) 'application/json'
    }catch{
     $err=@{error=[string]$_.Exception.Message;verified=$false}
     Respond $ctx 400 (ConvertTo-Json -InputObject $err -Compress) 'application/json'
    }
    continue
   }
   if($path -eq '/api/refresh'){
    $result=Fetch-Feeds
    $json=ConvertTo-Json -InputObject $result -Compress -Depth 10
    Respond $ctx 200 $json 'application/json';continue
   }
   $files=@{'/'='index.html';'/index.html'='index.html';'/styles.css'='styles.css';'/app.js'='app.js';'/materials-data.js'='materials-data.js';'/collection-core.js'='collection-core.js'}
   if(-not $files.ContainsKey($path)){Respond $ctx 404 '文件不存在' 'text/plain';continue}
   $filePath=Join-Path $root $files[$path]
   $type=if($path.EndsWith('.js')){'application/javascript'}elseif($path.EndsWith('.css')){'text/css'}else{'text/html'}
   Respond $ctx 200 ([IO.File]::ReadAllText($filePath,[Text.Encoding]::UTF8)) $type
  }catch{
   Write-Host ('请求处理错误：'+$_.Exception.Message) -ForegroundColor Red
   try{if($ctx.Response.OutputStream.CanWrite){Respond $ctx 500 '{"error":"数据采集或服务异常"}' 'application/json'}}catch{}
  }
 }
}finally{$listener.Stop();$listener.Close()}
