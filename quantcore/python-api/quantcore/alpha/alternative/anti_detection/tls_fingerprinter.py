import random
from typing import Dict, Optional

class TLSFingerprintManager:
    """TLS fingerprint obfuscation manager"""

    TLS_PROFILES = {
        "chrome_120_windows": {
            "name": "Chrome 120 on Windows",
            "cipher_suites": [
                "TLS_AES_128_GCM_SHA256",
                "TLS_AES_256_GCM_SHA384",
                "TLS_CHACHA20_POLY1305_SHA256",
                "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
                "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
                "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
                "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
            ],
            "curve_preferences": ["X25519", "P256", "P384"],
            "signature_algorithms": [
                "ecdsa_secp256r1_sha256",
                "rsa_pkcs1_sha256",
                "ecdsa_secp384r1_sha384",
                "rsa_pkcs1_sha384",
                "rsa_pkcs1_sha512",
                "ed25519",
            ],
            "ja3_hash": "771,4865-4866-4867-49195-49199-49196-49200,0-23-65281-10-11-35-16-5-51-43-13-45,29-23-24,0",
        },
        "firefox_121_linux": {
            "name": "Firefox 121 on Linux",
            "cipher_suites": [
                "TLS_AES_128_GCM_SHA256",
                "TLS_CHACHA20_POLY1305_SHA256",
                "TLS_AES_256_GCM_SHA384",
                "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
                "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
                "TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256",
                "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256",
            ],
            "curve_preferences": ["X25519", "P256", "P384", "P521"],
            "signature_algorithms": [
                "ecdsa_secp256r1_sha256",
                "ecdsa_secp384r1_sha384",
                "ecdsa_secp521r1_sha512",
                "rsa_pkcs1_sha256",
                "rsa_pkcs1_sha384",
                "rsa_pkcs1_sha512",
                "ed25519",
            ],
            "ja3_hash": "771,4865-4867-4866-49195-49199-49196-49200-52393-52392,0-23-65281-10-11-35-16-5-51-43-13-45,29-23-24,0",
        },
        "safari_17_macos": {
            "name": "Safari 17 on macOS",
            "cipher_suites": [
                "TLS_AES_128_GCM_SHA256",
                "TLS_AES_256_GCM_SHA384",
                "TLS_CHACHA20_POLY1305_SHA256",
            ],
            "curve_preferences": ["X25519", "P256", "P384"],
            "signature_algorithms": [
                "ecdsa_secp256r1_sha256",
                "ecdsa_secp384r1_sha384",
                "rsa_pkcs1_sha256",
                "rsa_pkcs1_sha384",
            ],
            "ja3_hash": "771,4865-4866-4867,0-23-65281-10-11-35-16-5-51-43-13-45,29-23-24,0",
        },
        "edge_120_windows": {
            "name": "Edge 120 on Windows (Chromium-based)",
            "cipher_suites": [
                "TLS_AES_128_GCM_SHA256",
                "TLS_AES_256_GCM_SHA384",
                "TLS_CHACHA20_POLY1305_SHA256",
                "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
                "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
                "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
                "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
            ],
            "curve_preferences": ["X25519", "P256", "P384"],
            "signature_algorithms": [
                "ecdsa_secp256r1_sha256",
                "rsa_pkcs1_sha256",
                "ecdsa_secp384r1_sha384",
                "rsa_pkcs1_sha384",
                "rsa_pkcs1_sha512",
                "ed25519",
            ],
            "ja3_hash": "771,4865-4866-4867-49195-49199-49196-49200,0-23-65281-10-11-35-16-5-51-43-13-45,29-23-24,0",
        },
        "mobile_chrome_android": {
            "name": "Chrome Mobile on Android",
            "cipher_suites": [
                "TLS_AES_128_GCM_SHA256",
                "TLS_AES_256_GCM_SHA384",
                "TLS_CHACHA20_POLY1305_SHA256",
            ],
            "curve_preferences": ["X25519", "P256"],
            "signature_algorithms": [
                "ecdsa_secp256r1_sha256",
                "rsa_pkcs1_sha256",
            ],
            "ja3_hash": "771,4865-4866-4867,0-23-65281-10-11-35-16-5-51-43-13-45,29-23-24,0",
        },
    }

    PROFILE_TO_BROWSER = {
        "chrome_120_windows": "chrome120",
        "firefox_121_linux": "firefox121",
        "safari_17_macos": "safari17",
        "edge_120_windows": "edge120",
        "mobile_chrome_android": "chrome100",
    }

    def __init__(self):
        self.current_profile: str = random.choice(list(self.TLS_PROFILES.keys()))
        self.profile_history: list = []
        self.rotation_count: int = 0

    def rotate_profile(self) -> str:
        """Rotate TLS profile"""
        available = [p for p in self.TLS_PROFILES.keys() if p != self.current_profile]
        new_profile = random.choice(available)

        self.profile_history.append(self.current_profile)
        if len(self.profile_history) > 10:
            self.profile_history.pop(0)

        self.current_profile = new_profile
        self.rotation_count += 1

        return new_profile

    def get_current_profile(self) -> Dict:
        """Get current TLS configuration"""
        return self.TLS_PROFILES[self.current_profile]

    def get_ja3_hash(self) -> str:
        """Get current JA3 fingerprint hash"""
        return self.get_current_profile().get("ja3_hash", "")

    def get_browser_type(self) -> str:
        """Map profile to browser type for curl_cffi"""
        return self.PROFILE_TO_BROWSER.get(self.current_profile, "chrome120")

    def apply_to_session(self, session) -> None:
        """Apply TLS config to HTTP session (using curl_cffi)"""
        session.impersonate = self.get_browser_type()
