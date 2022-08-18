import pytest

from ebmbot import signatures

from .time_helpers import TS, T


TS = TS.encode("utf8")
pytestmark = pytest.mark.freeze_time(T(10))


def test_validate_hmac_valid_signature():
    sig = signatures.generate_hmac(b"msg", b"secret")
    signatures.validate_hmac(b"msg", b"secret", sig)


def test_validate_hmac_invalid_signature():
    with pytest.raises(signatures.InvalidHMAC):
        signatures.validate_hmac(b"msg", b"secret", b"XYZ")


def test_validate_hmac_valid_timestamp_signature():
    sig = signatures.generate_hmac(TS, b"secret")
    signatures.validate_hmac(TS, b"secret", sig, max_age=15)


def test_validate_hmac_invalid_timestamp_signature():
    sig = signatures.generate_hmac(b"msg", b"secret")
    with pytest.raises(signatures.InvalidHMAC):
        signatures.validate_hmac(b"msg", b"secret", sig, max_age=30)


def test_validate_hmac_expired_timestamp_signature():
    sig = signatures.generate_hmac(TS, b"secret")
    with pytest.raises(signatures.InvalidHMAC):
        signatures.validate_hmac(TS, b"secret", sig, max_age=5)
