param(
    [int]$Port = 8765
)

Add-Type -AssemblyName System.Web

function Get-MimeType {
    param(
        [string]$Path
    )

    $extension = [System.IO.Path]::GetExtension($Path).ToLowerInvariant()
    switch ($extension) {
        ".pdf" { return "application/pdf" }
        ".mp4" { return "video/mp4" }
        ".webm" { return "video/webm" }
        ".ogg" { return "video/ogg" }
        ".mov" { return "video/quicktime" }
        ".m4v" { return "video/x-m4v" }
        ".mkv" { return "video/x-matroska" }
        ".mp3" { return "audio/mpeg" }
        ".wav" { return "audio/wav" }
        ".aac" { return "audio/aac" }
        ".m4a" { return "audio/mp4" }
        ".flac" { return "audio/flac" }
        ".png" { return "image/png" }
        ".jpg" { return "image/jpeg" }
        ".jpeg" { return "image/jpeg" }
        ".gif" { return "image/gif" }
        ".bmp" { return "image/bmp" }
        ".webp" { return "image/webp" }
        ".svg" { return "image/svg+xml" }
        default { return "application/octet-stream" }
    }
}

function Resolve-FullPath {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )

    try {
        return [System.IO.Path]::GetFullPath($Path)
    } catch {
        return $null
    }
}

function Test-IsWithinRoot {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Candidate
    )

    $normalizedRoot = Resolve-FullPath -Path $Root
    $normalizedCandidate = Resolve-FullPath -Path $Candidate
    if (-not $normalizedRoot -or -not $normalizedCandidate) {
        return $false
    }

    if ($normalizedRoot[-1] -ne [System.IO.Path]::DirectorySeparatorChar) {
        $normalizedRoot += [System.IO.Path]::DirectorySeparatorChar
    }

    return $normalizedCandidate.StartsWith($normalizedRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
        $normalizedCandidate.TrimEnd('\') -eq $normalizedRoot.TrimEnd('\')
}

function Get-RelativeChildPath {
    param(
        [string]$ChildFullPath,
        [string]$RootFullPath
    )

    $rootUri = New-Object System.Uri(($RootFullPath.TrimEnd('\') + '\'))
    $childUri = New-Object System.Uri($ChildFullPath)
    $relativeUri = $rootUri.MakeRelativeUri($childUri)
    return [System.Uri]::UnescapeDataString($relativeUri.ToString()).Replace('/', '\')
}

function Write-JsonResponse {
    param(
        [Parameter(Mandatory = $true)]$Response,
        [int]$StatusCode = 200,
        [Parameter(Mandatory = $true)]$Data
    )

    $json = $Data | ConvertTo-Json -Depth 8
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    $Response.StatusCode = $StatusCode
    $Response.ContentType = "application/json; charset=utf-8"
    $Response.ContentLength64 = $bytes.Length
    $Response.AddHeader("Access-Control-Allow-Origin", "*")
    $Response.AddHeader("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
    $Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $Response.Close()
}

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://127.0.0.1:$Port/")
$listener.Start()

Write-Host "Media local server listening on http://127.0.0.1:$Port/"

try {
    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response

        try {
            $path = $request.Url.AbsolutePath
            $queryText = $request.Url.Query
            if ($queryText.StartsWith("?")) {
                $queryText = $queryText.Substring(1)
            }
            $parsedQuery = [System.Web.HttpUtility]::ParseQueryString($queryText)

            if ($path -eq "/health") {
                $bytes = [System.Text.Encoding]::UTF8.GetBytes("ok")
                $response.StatusCode = 200
                $response.ContentType = "text/plain; charset=utf-8"
                $response.ContentLength64 = $bytes.Length
                $response.AddHeader("Access-Control-Allow-Origin", "*")
                $response.AddHeader("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
                $response.Close()
                continue
            }

            if ($request.HttpMethod -eq "OPTIONS") {
                $response.StatusCode = 204
                $response.AddHeader("Access-Control-Allow-Origin", "*")
                $response.AddHeader("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
                $response.AddHeader("Access-Control-Allow-Headers", "*")
                $response.Close()
                continue
            }

            if ($path -eq "/browse") {
                $rootPath = $parsedQuery.Get("root")
                $relativePath = $parsedQuery.Get("path")

                if ([string]::IsNullOrWhiteSpace($rootPath)) {
                    Write-JsonResponse -Response $response -StatusCode 400 -Data @{ error = "Missing root folder." }
                    continue
                }

                $rootFullPath = Resolve-FullPath -Path $rootPath
                if (-not $rootFullPath -or -not (Test-Path -LiteralPath $rootFullPath -PathType Container)) {
                    Write-JsonResponse -Response $response -StatusCode 404 -Data @{ error = "Root folder not found." }
                    continue
                }

                $currentFullPath = if ([string]::IsNullOrWhiteSpace($relativePath)) {
                    $rootFullPath
                } else {
                    Resolve-FullPath -Path (Join-Path $rootFullPath $relativePath)
                }

                if (-not $currentFullPath -or -not (Test-Path -LiteralPath $currentFullPath -PathType Container) -or -not (Test-IsWithinRoot -Root $rootFullPath -Candidate $currentFullPath)) {
                    Write-JsonResponse -Response $response -StatusCode 403 -Data @{ error = "Requested folder is outside root." }
                    continue
                }

                $folders = @(Get-ChildItem -LiteralPath $currentFullPath -Directory | Sort-Object Name | ForEach-Object {
                    @{
                        name = $_.Name
                        relativePath = Get-RelativeChildPath -ChildFullPath $_.FullName -RootFullPath $rootFullPath
                        fullPath = $_.FullName
                        type = "folder"
                    }
                })

                $files = @(Get-ChildItem -LiteralPath $currentFullPath -File | Sort-Object Name | ForEach-Object {
                    @{
                        name = $_.Name
                        relativePath = Get-RelativeChildPath -ChildFullPath $_.FullName -RootFullPath $rootFullPath
                        fullPath = $_.FullName
                        type = "file"
                    }
                })

                $rootFolders = @(Get-ChildItem -LiteralPath $rootFullPath -Directory | Sort-Object Name | ForEach-Object {
                    @{
                        name = $_.Name
                        relativePath = Get-RelativeChildPath -ChildFullPath $_.FullName -RootFullPath $rootFullPath
                    }
                })

                Write-JsonResponse -Response $response -Data @{
                    rootFolder = $rootFullPath
                    currentFolder = $currentFullPath
                    currentRelativePath = if ($currentFullPath -eq $rootFullPath) { "" } else { Get-RelativeChildPath -ChildFullPath $currentFullPath -RootFullPath $rootFullPath }
                    rootFolders = $rootFolders
                    folders = $folders
                    files = $files
                }
                continue
            }

            if ($path -ne "/media" -and $path -ne "/pdf") {
                $response.StatusCode = 404
                $response.Close()
                continue
            }

            $rawPath = $parsedQuery.Get("path")
            if ([string]::IsNullOrWhiteSpace($rawPath) -or -not (Test-Path -LiteralPath $rawPath)) {
                $response.StatusCode = 404
                $bytes = [System.Text.Encoding]::UTF8.GetBytes("File not found.")
                $response.ContentType = "text/plain; charset=utf-8"
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
                $response.Close()
                continue
            }

            $fileInfo = Get-Item -LiteralPath $rawPath
            $mimeType = Get-MimeType -Path $fileInfo.FullName
            $totalLength = [int64]$fileInfo.Length
            $rangeHeader = $request.Headers["Range"]
            $start = [int64]0
            $end = $totalLength - 1
            $statusCode = 200

            if ($rangeHeader -and $rangeHeader.StartsWith("bytes=")) {
                $parts = $rangeHeader.Substring(6).Split("-", 2)
                if ($parts[0]) {
                    $start = [int64]$parts[0]
                }
                if ($parts.Count -gt 1 -and $parts[1]) {
                    $end = [int64]$parts[1]
                }

                if ($start -lt 0 -or $end -ge $totalLength -or $start -gt $end) {
                    $response.StatusCode = 416
                    $response.AddHeader("Content-Range", "bytes */$totalLength")
                    $response.Close()
                    continue
                }

                $statusCode = 206
            }

            $contentLength = $end - $start + 1
            $response.StatusCode = $statusCode
            $response.ContentType = $mimeType
            $response.ContentLength64 = $contentLength
            $response.AddHeader("Accept-Ranges", "bytes")
            $response.AddHeader("Cache-Control", "no-store")
            $response.AddHeader("Access-Control-Allow-Origin", "*")
            $response.AddHeader("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
            if ($statusCode -eq 206) {
                $response.AddHeader("Content-Range", "bytes $start-$end/$totalLength")
            }

            $stream = [System.IO.File]::OpenRead($fileInfo.FullName)
            try {
                $stream.Seek($start, [System.IO.SeekOrigin]::Begin) | Out-Null
                $buffer = New-Object byte[] (64KB)
                $remaining = $contentLength
                while ($remaining -gt 0) {
                    $toRead = [Math]::Min($buffer.Length, $remaining)
                    $read = $stream.Read($buffer, 0, $toRead)
                    if ($read -le 0) {
                        break
                    }
                    $response.OutputStream.Write($buffer, 0, $read)
                    $remaining -= $read
                }
            } finally {
                $stream.Dispose()
                $response.OutputStream.Dispose()
            }
        } catch {
            try {
                $response.StatusCode = 500
                $bytes = [System.Text.Encoding]::UTF8.GetBytes($_.Exception.Message)
                $response.ContentType = "text/plain; charset=utf-8"
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
                $response.Close()
            } catch {
            }
        }
    }
} finally {
    $listener.Stop()
    $listener.Close()
}
