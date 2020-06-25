import hmac
import time


class InvalidHMAC(Exception):
    pass


def generate_hmac(msg, secret):
    return hmac.new(secret, msg, digestmod="sha1").hexdigest().encode("utf8")


def validate_hmac(msg, secret, signature, max_age=None):
    mac = generate_hmac(msg, secret)
    if not hmac.compare_digest(mac, signature):
        raise InvalidHMAC("Signature does not match")

    if max_age is None:
        return

    try:
        timestamp = float(msg)
    except ValueError:
        raise InvalidHMAC("Invalid timestamp")

    if time.time() - timestamp > max_age:
        raise InvalidHMAC("Expired")
