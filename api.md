# Ksem API Dokumentation

> Diese Doku enthält alle HTTP-/WebSocket-Endpunkte der Ksem-Komponente aus deinen HAR-Dateien (ohne Frontend/Assets).

---

## Authentifizierung & Benutzer

### Login

- **Methode:** POST
- **Pfad:** `/api/login`
- **Request:**
    ```json
    {
      "user": "admin",
      "password": "geheim"
    }
    ```
- **Response:**
    ```json
    {
      "access_token": "abcdefg1234567",
      "token_type": "Bearer",
      "expires_in": 3600
    }
    ```
- **Hinweis:**  
  Der Token ist im Header `Authorization: Bearer <token>` anzugeben.

---



## Api Abfragen










### Benutzerinfo

- **Methode:** GET
- **Pfad:** `/api/user/info`
- **Header:**  
    `Authorization: Bearer <token>`
- **Response:**
    ```json
    {
      "user": "admin",
      "roles": ["admin", "user"],
      "last_login": "2024-07-10T06:30:01Z"
    }
    ```

---

### Passwort ändern

- **Methode:** POST
- **Pfad:** `/api/user/change_password`
- **Header:**  
    `Authorization: Bearer <token>`
- **Request:**
    ```json
    {
      "old_password": "alt",
      "new_password": "neu"
    }
    ```
- **Response:**
    ```json
    { "result": "ok" }
    ```

---
## Wallbox & E-Mobility (evse-kostal & e-mobility)

### Wallbox-Liste abrufen

- **Methode:** GET
- **Pfad:** `/api/e-mobility/wallbox/list`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    [
      {
        "id": "0b6bef8f-c578-4ab3-9ce2-11111111",
        "name": "Wallbox Garage",
        "model": "KSEM-EVSE-22",
        "state": "ready"
      }
      // ggf. weitere Wallboxen
    ]
    ```

---

### Wallbox-Details abrufen

- **Methode:** GET
- **Pfad:** `/api/e-mobility/wallbox/details/{wallbox_id}`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    {
      "id": "0b6bef8f-c578-4ab3-9ce2-a054111111",
      "name": "Wallbox Garage",
      "model": "KSEM-EVSE-22",
      "state": "ready",
      "plug": true,
      "charging": false,
      "error": null,
      "max_current": 16,
      "actual_current": 0,
      "mode": "manual",
      "rfid": null,
      "cable_locked": true,
      "temperature": 32.5,
      "firmware": "1.2.3",
      "last_session": {
        "start": "2024-07-10T14:32:11Z",
        "stop": "2024-07-10T15:02:55Z",
        "energy": 7.2,
        "charged_by": "RFID123456"
      },
      "sessions": [
        {
          "start": "2024-07-09T17:15:20Z",
          "stop": "2024-07-09T18:00:10Z",
          "energy": 10.5,
          "charged_by": "RFID123456"
        }
      ]
    }
    ```

---

### Wallbox-Status abrufen

- **Methode:** GET
- **Pfad:** `/api/e-mobility/wallbox/state/{wallbox_id}`
- **Header:** `Authorization: Bearer <token>`
- **Response:** *(kann ähnlich Details sein, mit Schwerpunkt auf Status)*
    ```json
    {
      "state": "charging",
      "plug": true,
      "charging": true,
      "actual_current": 16,
      "power": 3600,
      "error": null
    }
    ```

---

### Wallbox-Historie

- **Methode:** GET
- **Pfad:** `/api/e-mobility/wallbox/history/{wallbox_id}?limit=10`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    [
      {
        "start": "2024-07-10T14:32:11Z",
        "stop": "2024-07-10T15:02:55Z",
        "energy": 7.2,
        "charged_by": "RFID123456"
      }
      // ...
    ]
    ```

---

### Wallbox-Einstellungen lesen/schreiben

- **Methode:** GET / PUT
- **Pfad:** `/api/e-mobility/wallbox/settings/{wallbox_id}`
- **Header:** `Authorization: Bearer <token>`
- **GET Response:**
    ```json
    {
      "max_current": 16,
      "min_current": 6,
      "phases": 3,
      "charging_modes": ["manual", "auto", "smart"],
      "default_mode": "auto",
      "cable_locked": true,
      "allowed_rfids": ["RFID123456"]
    }
    ```
- **PUT Request:**
    ```json
    { "default_mode": "smart" }
    ```
- **PUT Response:**
    ```json
    { "result": "ok" }
    ```

---

### Wallbox Steuerbefehl (Aktion: Start, Stop, Lock, Unlock, Reset)

- **Methode:** POST
- **Pfad:** `/api/e-mobility/wallbox/command/{wallbox_id}`
- **Header:** `Authorization: Bearer <token>`
- **Request:**
    ```json
    { "action": "start" }
    ```
- **Response:**
    ```json
    { "result": "ok" }
    ```

---

### Wallbox Firmware-Info

- **Methode:** GET
- **Pfad:** `/api/e-mobility/wallbox/firmware/{wallbox_id}`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    {
      "version": "1.2.3",
      "update_available": false,
      "release_notes": ""
    }
    ```

---

### Wallbox Diagnose

- **Methode:** GET
- **Pfad:** `/api/e-mobility/wallbox/diagnose/{wallbox_id}`
- **Header:** `Authorization: Bearer <token>`
- **Response:** *(vereinfachtes Beispiel)*
    ```json
    {
      "diagnostics": [
        {"name": "Temperature Sensor", "status": "ok"},
        {"name": "Contactor", "status": "ok"}
      ]
    }
    ```

---

### Wallbox Benachrichtigungen

- **Methode:** GET
- **Pfad:** `/api/e-mobility/wallbox/notifications/{wallbox_id}`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    [
      {"timestamp": "2024-07-10T12:00:00Z", "text": "Ladekabel getrennt"}
    ]
    ```

---

### Wallbox Fehlerliste

- **Methode:** GET
- **Pfad:** `/api/e-mobility/wallbox/errors/{wallbox_id}`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    [
      { "timestamp": "2024-07-09T18:02:00Z", "code": 102, "text": "Residual current error" }
    ]
    ```

---

### Wallbox Statistik

- **Methode:** GET
- **Pfad:** `/api/e-mobility/wallbox/statistics/{wallbox_id}`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    {
      "sessions": 245,
      "energy_total": 2350.4,
      "max_power": 11500,
      "total_duration": 162000 // Sekunden
    }
    ```

---

### Wallbox Phasenstatus

- **Methode:** GET
- **Pfad:** `/api/evse-kostal/evse/{evse_id}/phases`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    {
      "phases": [
        { "phase": 1, "current": 16, "voltage": 228 },
        { "phase": 2, "current": 0,  "voltage": 0 },
        { "phase": 3, "current": 16, "voltage": 229 }
      ]
    }
    ```

---

### (Weitere, identische Endpunkte – z. B. /evse-kostal/evse/{evse_id}/details, /settings, /setpoints, /commands, /sessions – siehe oben, identischer Aufbau wie e-mobility.)

---
## Smartmeter

### Smartmeter-Liste abrufen

- **Methode:** GET
- **Pfad:** `/api/smartmeter/list`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    [
      {
        "id": "KSEM-001-SM01",
        "name": "Smartmeter Keller",
        "model": "KSEM-SM1"
      }
      // ggf. weitere Smartmeter
    ]
    ```

---

### Smartmeter-Status abrufen

- **Methode:** GET
- **Pfad:** `/api/smartmeter/KSEM-001-SM01/status`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    {
      "id": "KSEM-001-SM01",
      "name": "KSEM Smartmeter",
      "model": "KSEM-SM1",
      "power": 327,
      "energy_total": 3456.2,
      "energy_export": 203.4,
      "energy_import": 3252.8,
      "voltage": 229,
      "current": 1.7,
      "frequency": 50.02,
      "timestamp": "2024-07-10T15:05:34Z"
    }
    ```

---

### Smartmeter-Einstellungen lesen/schreiben

- **Methode:** GET / PUT
- **Pfad:** `/api/smartmeter/KSEM-001-SM01/settings`
- **Header:** `Authorization: Bearer <token>`
- **GET Response:**
    ```json
    {
      "measurement_interval": 10,
      "voltage_range": [200, 240],
      "phases": 3,
      "location": "Keller"
    }
    ```
- **PUT Request:**
    ```json
    { "measurement_interval": 5 }
    ```
- **PUT Response:**
    ```json
    { "result": "ok" }
    ```

---

### Smartmeter-Log abrufen

- **Methode:** GET
- **Pfad:** `/api/smartmeter/KSEM-001-SM01/log`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    [
      { "timestamp": "2024-07-09T18:05:00Z", "event": "reset", "user": "admin" }
    ]
    ```

---
## System & Device Endpunkte

### System-/API-Version abrufen

- **Methode:** GET
- **Pfad:** `/api/version`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    {
      "version": "2.1.0",
      "api_version": "v1"
    }
    ```

---

### Geräteinfo abrufen

- **Methode:** GET
- **Pfad:** `/api/device/info`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    {
      "device_id": "KSEM-001-MAIN",
      "model": "KSEM-Core",
      "serial": "KSEM-2024-0001",
      "location": "Hausanschlussraum",
      "uptime": 345632,
      "firmware": "2.1.0"
    }
    ```

---

### Gerätestatus/Health abrufen

- **Methode:** GET
- **Pfad:** `/api/device/health`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    {
      "device_id": "KSEM-001-MAIN",
      "status": "ok",
      "last_restart": "2024-07-10T00:02:01Z",
      "free_memory": 30238,
      "cpu_load": 0.32,
      "temperature": 41.2
    }
    ```

---

### Gerät neustarten

- **Methode:** POST
- **Pfad:** `/api/device/reboot`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    { "result": "ok", "rebooting": true }
    ```

---

### System-Log abrufen

- **Methode:** GET
- **Pfad:** `/api/log/system`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    [
      { "timestamp": "2024-07-10T09:11:00Z", "level": "info", "message": "System start" },
      { "timestamp": "2024-07-10T10:32:12Z", "level": "warn", "message": "Low memory" }
    ]
    ```

---

### Geräte-Log abrufen

- **Methode:** GET
- **Pfad:** `/api/log/device`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    [
      { "timestamp": "2024-07-10T11:12:00Z", "level": "info", "message": "Wallbox charging started" }
    ]
    ```

---

### System-Benachrichtigungen abrufen

- **Methode:** GET
- **Pfad:** `/api/notifications`
- **Header:** `Authorization: Bearer <token>`
- **Response:**
    ```json
    [
      { "timestamp": "2024-07-10T12:00:00Z", "text": "Neue Firmware verfügbar" }
    ]
    ```

---
## WebSocket-Verbindung – Authentifizierung

Beim Aufbau der WebSocket-Verbindung muss
1. der **Token im HTTP-Header** (`Authorization: Bearer <token>`) gesendet werden
2. **direkt nach dem Verbindungsaufbau** eine Nachricht mit dem exakten Inhalt  
   `"Bearer <token>"`  
   (also als reiner String, **nicht** als JSON!)  
   an den Server geschickt werden.

---

**Schritte:**

1. **Verbindung aufbauen:**  
   - Sende HTTP-Header:  
     ```
     Authorization: Bearer <access_token>
     ```
2. **Direkt nach Verbindungsaufbau:**  
   - Sende als **erste Nachricht** über die WS-Verbindung:  
     ```
     Bearer <access_token>
     ```
     *(Ohne Anführungszeichen, exakt mit Leerzeichen dazwischen, reiner String!)*

3. **Nach erfolgreicher Authentifizierung:**  
   - Empfang der Event- oder Statusdaten als Protobuf (binary) oder JSON.

---

### Pseudocode

```text
1. Open WebSocket to ws://<host>/api/data-transfer/ws/protobuf/gdr/local/values/KSEM-001-WB01/evse
2. Send header: Authorization: Bearer <token>
3. After connect, send string: "Bearer <token>"
4. Wait for incoming data
````
## WebSocket: Wallbox Live-Werte

**Pfad:**  
`ws://<host>/api/data-transfer/ws/protobuf/gdr/local/values/+/evse`
### Beschreibung & Datenstruktur

- Die Verbindung liefert alle aktuellen Messwerte und Statusdaten der jeweiligen Wallbox(en) in **Protobuf-Binärformat**.
- Die Nachrichten werden nach Decodierung (im Frontend via `gdr.GDRs.decode(...)`) in einem **Dictionary `GDRs`** abgelegt.
- **Jede Wallbox (EVSE) wird als eigenes Objekt gespeichert, Key ist die UUID:**


```json
{
"GDRs": {
  "0b6bef8f-c578-4ab3-9ce2-a05418f7ca3": {
    "id": "0b6bef8f-c578-4ab3-9ce2-a05418f7fca3",      // Wallbox-UUID
    "status": 1,                                       // Statuscode (z. B. 1 = ready, 2 = charging, etc.)
    "timestamp": 1752254953,                           // Unix-Timestamp (Sekunden)
    "values": {                                        // Messwerte, meist OBIS-Code als Key
      "1-0:32.4.0*255": 229,                           // Beispiel: Spannung (V)
      "1-0:31.7.0*255": 16,                            // Beispiel: Strom (A)
      ...
    },
    "flexValues": {                                    // Spezialwerte, als Key meist Klartext-String
      "evse_error_code": {
        // Ggf. Fehlerdetails als Objekt, sonst leer bei kein Fehler
      },
      ...
    }
  },
  ...
}
}
```


## WebSocket: Wallbox State-Stream (JSON)

**Pfad:**  
`ws://<host>/api/data-transfer/ws/json/json/local/evse/+/state`
(`+` steht für die jeweilige Wallbox-UUID bei Plus werden alle gesendet)

---

### Beschreibung

- Überträgt Echtzeit-Statusänderungen der jeweiligen Wallbox(en) als kompaktes JSON-Objekt.
- Für jede State-Änderung oder bei bestimmten Ereignissen wird eine Nachricht gesendet.

---

### Beispiel für empfangene Nachricht

```json
{
  "topic": "json/local/evse/0b6bef8f-c578-4ab3-9ce3-a05418f7cc3/state",
  "msg": {
    "evse-id": "0b6bef8f-c578-4ab3-9ce3-a05418f7fcc3",
    "parentState": "",
    "state": "stateConnected"
  }
}
```

## WebSocket: Charge-Mode-Stream (Wallboxen)

**Pfad:**  
`ws://<host>/api/data-transfer/ws/json/json/local/config/e-mobility/chargemode`

### Beschreibung

- Dieser Stream überträgt in Echtzeit den aktuellen Lademodus und zugehörige Steuerparameter für die Wallbox(en).
- Eine Nachricht wird gesendet, wenn sich der Modus oder eine der Quoten-Einstellungen ändert (z. B. durch Benutzeraktion oder externe Steuerung).
- Der Channel liefert keine Messwerte, sondern ausschließlich die aktuell eingestellte Betriebsart und Steuerinformationen für den Lademodus.

### **Beispiel für empfangene Nachricht**

```json
{
  "topic": "json/local/config/e-mobility/chargemode",
  "msg": {
    "mode": "lock",
    "mincharginpowerquota": 0,
    "minpvpowerquota": 0,
    "lastminchargingpowerquota": 100,
    "lastminpvpowerquota": 30,
    "controlledby": 0
  }
}
