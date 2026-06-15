import urllib.request
import socks
import socket

# تست SOCKS5 روی پورت 10808
socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 10808)
socket.socket = socks.socksocket
try:
    response = urllib.request.urlopen("https://api.ipify.org", timeout=10)
    print("✅ پروکسی SOCKS5 کار می‌کند. IP:", response.read().decode())
except Exception as e:
    print("❌ SOCKS5 خطا:", e)

# تست HTTP روی پورت 10809 (اگر فعال است)
try:
    proxy_handler = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:10809', 'https': 'http://127.0.0.1:10809'})
    opener = urllib.request.build_opener(proxy_handler)
    response = opener.open("https://api.ipify.org", timeout=10)
    print("✅ پروکسی HTTP کار می‌کند. IP:", response.read().decode())
except Exception as e:
    print("❌ HTTP خطا:", e)