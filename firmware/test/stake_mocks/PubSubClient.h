#pragma once
#include "WiFi.h"
/* Broker mock: retained command for the stake (mock_retained_down) and an inbox of
 * (topic, payload) for the gateway; publishes go to mock_pub, one "topic json" per line. */
struct PubSubClient {
  void (*cb)(char *, byte *, unsigned int) = nullptr; bool con = false, sub = false, delivered = false;
  PubSubClient(WiFiClient &) {}
  void setServer(const char *, int) {} void setCallback(void (*c)(char *, byte *, unsigned int)) { cb = c; }
  void setBufferSize(int) {}
  bool connect(const char *) { con = WiFi.status() == WL_CONNECTED; sub = false; return con; }
  int state() { return con ? 0 : -2; }
  bool connected() { if (WiFi.status() != WL_CONNECTED) con = false; return con; }
  void disconnect() { con = false; }
  bool subscribe(const char *) { sub = true; delivered = false; return true; }
  bool loop() {
    if (!connected() || !sub || !cb) return con;
    if (!delivered && !mock_retained_down.empty()) {
      delivered = true;
      cb((char *)"down", (byte *)mock_retained_down.data(), (unsigned)mock_retained_down.size()); }
    while (!mock_mqtt_inbox.empty()) { auto m = mock_mqtt_inbox.front(); mock_mqtt_inbox.erase(mock_mqtt_inbox.begin());
      cb((char *)m.first.c_str(), (byte *)m.second.data(), (unsigned)m.second.size()); }
    return con; }
  bool publish(const char *t, const char *p, bool retained = false) {
    if (!connected()) return false;
    fprintf(mock_pub, "%s %s\n", t, p);
    mock_publish_count++;
    return true;
  }
};
