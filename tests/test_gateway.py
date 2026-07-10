
from omniforge.config import Settings
from omniforge.gateway.policy import authorize_export


def test_fail_open():
    s = Settings(production_strict=False, omniforge_gateway_fail_open=True)
    d = authorize_export(s)
    assert d.allowed


def test_production_strict_denies():
    s = Settings(production_strict=True, omniforge_gateway_fail_open=True)
    d = authorize_export(s)
    assert not d.allowed
