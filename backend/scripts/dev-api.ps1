# Ayudas para probar la API de VIGIA a mano desde PowerShell (SOLO desarrollo, con emuladores).
#
# Cargar en la terminal actual (desde la raíz del proyecto):
#     . .\scripts\dev-api.ps1
#
# Ejemplos:
#     $marta = New-VigiaUser "marta@example.com"
#     Vigia POST /auth/register $marta @{ displayName = "Marta" }
#     Vigia GET /me $marta

$script:VigiaApi = "http://127.0.0.1:8000/v1"
$script:AuthEmulator = "http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1"

function New-VigiaUser {
    <# Crea una cuenta en el emulador de Auth (o inicia sesión si ya existe) y devuelve sus encabezados. #>
    param([Parameter(Mandatory)][string]$Email, [string]$Password = "clave123")
    $body = @{ email = $Email; password = $Password; returnSecureToken = $true } | ConvertTo-Json
    try {
        $r = Invoke-RestMethod -Method Post "$script:AuthEmulator/accounts:signUp?key=demo" -ContentType "application/json" -Body $body
    } catch {
        $r = Invoke-RestMethod -Method Post "$script:AuthEmulator/accounts:signInWithPassword?key=demo" -ContentType "application/json" -Body $body
    }
    @{ Authorization = "Bearer $($r.idToken)" }
}

function Vigia {
    <# Llama a la API y muestra el código HTTP y la respuesta. Devuelve el objeto de respuesta (o $null si hubo error). #>
    param(
        [Parameter(Mandatory)][ValidateSet("GET", "POST", "PATCH", "DELETE")][string]$Method,
        [Parameter(Mandatory)][string]$Path,
        [hashtable]$Headers = @{},
        $Body = $null
    )
    $params = @{ Method = $Method; Uri = "$script:VigiaApi$Path"; Headers = $Headers; UseBasicParsing = $true }
    if ($null -ne $Body) {
        $params.ContentType = "application/json; charset=utf-8"
        $params.Body = [Text.Encoding]::UTF8.GetBytes(($Body | ConvertTo-Json -Depth 6))
    }
    try {
        $response = Invoke-WebRequest @params
        $code = [int]$response.StatusCode
        $text = [Text.Encoding]::UTF8.GetString($response.RawContentStream.ToArray())
    } catch {
        if (-not $_.Exception.Response) { throw }
        $code = [int]$_.Exception.Response.StatusCode
        $text = $_.ErrorDetails.Message
    }
    $color = if ($code -lt 300) { "Green" } elseif ($code -lt 500) { "Yellow" } else { "Red" }
    Write-Host "$Method $Path -> $code" -ForegroundColor $color
    if (-not $text) { return }
    $data = $text | ConvertFrom-Json
    Write-Host ($data | ConvertTo-Json -Depth 6)
    if ($code -lt 300) { return $data }
}
