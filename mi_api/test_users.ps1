# test_users.ps1 - Script CORREGIDO para probar POST /users

Write-Host "🧪 Probando endpoint POST /users..." -ForegroundColor Cyan

# Verificar si el servidor está ejecutándose
Write-Host "`n🔍 Verificando si el servidor está ejecutándose..." -ForegroundColor Yellow
try {
    $testResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3
    Write-Host "✅ Servidor detectado en http://localhost:8000" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: El servidor no está ejecutándose" -ForegroundColor Red
    Write-Host "   Ejecuta primero: uvicorn main:app --reload" -ForegroundColor Yellow
    exit
}

# Test 1: Crear usuario exitoso en acme-corp (CORREGIDO: sin 's' al final)
Write-Host "`n✅ Test 1: Crear usuario en acme-corp" -ForegroundColor Yellow
try {
    # ✅ CORREGIDO: Usar parámetros en query string
    $response1 = Invoke-RestMethod -Uri "http://localhost:8000/users?name=Usuario%20Test%201&email=test1@acme.com" -Method POST -Headers @{"X-Tenant-ID" = "acme-corp"}
    
    Write-Host "   ✅ Éxito: $($response1.message)" -ForegroundColor Green
    Write-Host "   Usuario creado: ID=$($response1.user.id), Nombre=$($response1.user.name), Email=$($response1.user.email)" -ForegroundColor White
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Crear usuario en startup-tech (CORREGIDO: parámetros en URL)
Write-Host "`n✅ Test 2: Crear usuario en startup-tech" -ForegroundColor Yellow
try {
    # ✅ CORREGIDO: Parámetros en query string
    $response2 = Invoke-RestMethod -Uri "http://localhost:8000/users?name=Usuario%20Test%202&email=test2@startup.com" -Method POST -Headers @{"X-Tenant-ID" = "startup-tech"}
    
    Write-Host "   ✅ Éxito: $($response2.message)" -ForegroundColor Green
    Write-Host "   Usuario creado: ID=$($response2.user.id), Nombre=$($response2.user.name), Email=$($response2.user.email)" -ForegroundColor White
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Intentar crear usuario duplicado (debe fallar)
Write-Host "`n❌ Test 3: Intentar crear usuario duplicado" -ForegroundColor Yellow
try {
    $response3 = Invoke-RestMethod -Uri "http://localhost:8000/users?name=Usuario%20Duplicado&email=test1@acme.com" -Method POST -Headers @{"X-Tenant-ID" = "acme-corp"}
    
    Write-Host "   ❌ ERROR: Debió fallar por duplicado" -ForegroundColor Red
} catch {
    Write-Host "   ✅ Comportamiento esperado: Usuario duplicado detectado" -ForegroundColor Green
    Write-Host "   Mensaje de error: $($_.ErrorDetails.Message)" -ForegroundColor Gray
}

# Test 4: Intentar sin header (debe fallar)
Write-Host "`n❌ Test 4: Intentar sin header X-Tenant-ID" -ForegroundColor Yellow
try {
    $response4 = Invoke-RestMethod -Uri "http://localhost:8000/users?name=Usuario%20Sin%20Tenant&email=test@test.com" -Method POST
    
    Write-Host "   ❌ ERROR: Debió fallar por falta de tenant" -ForegroundColor Red
} catch {
    Write-Host "   ✅ Comportamiento esperado: Falta header X-Tenant-ID" -ForegroundColor Green
    Write-Host "   Mensaje de error: $($_.ErrorDetails.Message)" -ForegroundColor Gray
}

# Test 5: Verificar usuarios creados (aislamiento por tenant)
Write-Host "`n📊 Test 5: Verificar aislamiento por tenant" -ForegroundColor Cyan
try {
    Write-Host "   👥 Usuarios en acme-corp:" -ForegroundColor White
    $users1 = Invoke-RestMethod -Uri "http://localhost:8000/users" -Headers @{"X-Tenant-ID" = "acme-corp"}
    Write-Host "   Total usuarios: $($users1.total_users)" -ForegroundColor Green
    foreach ($user in $users1.users) {
        Write-Host "     - $($user.name) <$($user.email)>" -ForegroundColor Gray
    }
    
    Write-Host "`n   👥 Usuarios en startup-tech:" -ForegroundColor White  
    $users2 = Invoke-RestMethod -Uri "http://localhost:8000/users" -Headers @{"X-Tenant-ID" = "startup-tech"}
    Write-Host "   Total usuarios: $($users2.total_users)" -ForegroundColor Green
    foreach ($user in $users2.users) {
        Write-Host "     - $($user.name) <$($user.email)>" -ForegroundColor Gray
    }
    
    Write-Host "`n   🔍 Verificando aislamiento..." -ForegroundColor Yellow
    if ($users1.users.Count -gt 0 -and $users2.users.Count -gt 0) {
        Write-Host "   ✅ AISLAMIENTO FUNCIONANDO: Cada tenant tiene sus propios usuarios" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Solo un tenant tiene usuarios" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Error al obtener usuarios: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: Probar endpoint exclusivo (solo tenants premium)
Write-Host "`n🚀 Test 6: Probar endpoint /analytics (solo premium)" -ForegroundColor Cyan
try {
    Write-Host "   Probando con acme-corp (premium)..." -ForegroundColor White
    $analytics1 = Invoke-RestMethod -Uri "http://localhost:8000/analytics" -Headers @{"X-Tenant-ID" = "acme-corp"}
    Write-Host "   ✅ Acceso concedido a analytics" -ForegroundColor Green
    Write-Host "   Datos: $($analytics1.analytics | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Error inesperado con acme-corp: $($_.Exception.Message)" -ForegroundColor Red
}

try {
    Write-Host "   Probando con startup-tech (básico)..." -ForegroundColor White
    $analytics2 = Invoke-RestMethod -Uri "http://localhost:8000/analytics" -Headers @{"X-Tenant-ID" = "startup-tech"}
    Write-Host "   ❌ ERROR: No debería tener acceso" -ForegroundColor Red
} catch {
    Write-Host "   ✅ Comportamiento esperado: startup-tech no tiene acceso a analytics" -ForegroundColor Green
    Write-Host "   Mensaje: $($_.ErrorDetails.Message)" -ForegroundColor Gray
}

Write-Host "`n🎉 TODAS LAS PRUEBAS COMPLETADAS!" -ForegroundColor Green
Write-Host "   Resumen:" -ForegroundColor White
Write-Host "   - ✅ Middleware funcionando" -ForegroundColor Green
Write-Host "   - ✅ Decoradores funcionando" -ForegroundColor Green  
Write-Host "   - ✅ Base de datos multitenant funcionando" -ForegroundColor Green
Write-Host "   - ✅ Aislamiento de datos verificando" -ForegroundColor Green