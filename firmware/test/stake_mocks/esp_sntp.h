#pragma once
typedef enum { SNTP_SYNC_STATUS_RESET, SNTP_SYNC_STATUS_COMPLETED, SNTP_SYNC_STATUS_IN_PROGRESS } sntp_sync_status_t;
inline sntp_sync_status_t mock_sntp;
inline void sntp_set_sync_status(sntp_sync_status_t s) { mock_sntp = s; }
inline sntp_sync_status_t sntp_get_sync_status() { return mock_sntp; }
inline void configTime(long, int, const char *, const char *) {
  if (WiFi.status() != WL_CONNECTED) return;
  delay(300); mock_epoch = 1794659400LL - mock_us / 1000000; mock_sntp = SNTP_SYNC_STATUS_COMPLETED; }
