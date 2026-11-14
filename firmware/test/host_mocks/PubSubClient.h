#pragma once
#include "WiFi.h"
extern bool mock_online; extern FILE *mock_pub;
struct PubSubClient {
  void (*cb)(char *, byte *, unsigned int) = nullptr;
  PubSubClient(WiFiClient &) {}
  bool connected() { return mock_online; }
  bool connect(const char *) { return mock_online; }
  bool subscribe(const char *) { return true; }
  bool loop() { return true; }
  void setServer(const char *, int) {}
  void setCallback(void (*c)(char *, byte *, unsigned int)) { cb = c; }
  void setBufferSize(int) {}
  bool publish(const char *t, const char *p) { fprintf(mock_pub, "%s %s\n", t, p); return true; }
};
