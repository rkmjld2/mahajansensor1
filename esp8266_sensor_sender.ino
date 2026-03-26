#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>

const char* ssid = "Airtel_56";
const char* password = "Raviuma5658";

// === YOUR RECEIVER APP URL ===
const char* receiverUrl = "https://mahajansesor1.streamlit.app/";

// === YOUR SECRET KEY (Cleaned from your command prompt) ===
const char* secretKey = "12b5112c62284ea0b3da0039f298ec7a85ac9a1791044052b6df970640afb1c5";

#include <DHT.h>
#define DHTPIN 2
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

unsigned long previousMillis = 0;
const long interval = 15000;

void setup() {
  Serial.begin(115200);
  dht.begin();
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
}

void loop() {
  if (millis() - previousMillis >= interval) {
    previousMillis = millis();

    float temp = dht.readTemperature();
    float hum = dht.readHumidity();

    if (!isnan(temp) && !isnan(hum)) {
      sendSecureData(temp, hum);
    }
  }
}

void sendSecureData(float temp, float hum) {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClientSecure client;
    client.setInsecure();

    HTTPClient http;

    String url = String(receiverUrl) +
                 "?temperature=" + String(temp, 2) +
                 "&humidity=" + String(hum, 2) +
                 "&device_id=ESP8266_01" +
                 "&key=" + String(secretKey);

    Serial.println("Sending: " + url);

    http.begin(client, url);
    int httpCode = http.GET();

    if (httpCode > 0) {
      Serial.printf("✅ Sent: %.2f°C | %.2f%%  → Code: %d\n", temp, hum, httpCode);
    } else {
      Serial.println("❌ Send Failed");
    }
    http.end();
  }
}