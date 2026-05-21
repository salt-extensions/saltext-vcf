"""Shared pytest fixtures for saltext-vcf unit tests."""

import pytest
import responses as responses_lib


@pytest.fixture
def opts():
    """Salt-style opts dict with all three components configured for the test host."""
    return {
        "pillar": {
            "saltext.vcf": {
                "vcenter": {
                    "host": "vc.test",
                    "username": "u",
                    "password": "p",
                    "verify_ssl": False,
                },
                "sddc_manager": {
                    "host": "sm.test",
                    "username": "u",
                    "password": "p",
                    "verify_ssl": False,
                },
                "nsx": {
                    "host": "nsx.test",
                    "username": "u",
                    "password": "p",
                    "verify_ssl": False,
                },
                "esxi": {
                    "host": "esxi.test",
                    "username": "root",
                    "password": "p",
                    "verify_ssl": False,
                },
                "vcf_ops": {
                    "host": "ops.test",
                    "username": "admin",
                    "password": "p",
                    "verify_ssl": False,
                },
                "vcf_installer": {
                    "host": "installer.test",
                    "username": "admin",
                    "password": "p",
                    "verify_ssl": False,
                },
                "profiles": {
                    "alt": {
                        "vcenter": {
                            "host": "vc.alt",
                            "username": "u2",
                            "password": "p2",
                            "verify_ssl": False,
                        },
                    },
                },
            },
        },
        "test": False,
    }


@pytest.fixture
def mocked_responses():
    """Wraps the global `responses` library context for HTTP mocking."""
    with responses_lib.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps


@pytest.fixture(autouse=True)
def reset_caches():
    """Clear util-level session/token caches between tests."""
    from saltext.vcf.utils import cim
    from saltext.vcf.utils import esxi
    from saltext.vcf.utils import installer
    from saltext.vcf.utils import sddc
    from saltext.vcf.utils import vcenter
    from saltext.vcf.utils import vcfops
    from saltext.vcf.utils import vim as soap
    from saltext.vcf.utils import vsan

    caches = [
        vcenter._SESSION_CACHE,
        sddc._TOKEN_CACHE,
        esxi._SI_CACHE,
        vcfops._TOKEN_CACHE,
        installer._SESSION_CACHE,
        soap._SI_CACHE,
        cim._CONN_CACHE,
        vsan._VSAN_STUB_CACHE,
    ]
    for c in caches:
        c.clear()
    yield
    for c in caches:
        c.clear()


@pytest.fixture
def vcenter_authed(mocked_responses):
    """Pre-register the vCenter /api/session POST so modules can authenticate."""
    mocked_responses.add(
        responses_lib.POST,
        "https://vc.test/api/session",
        json="session-token-abc",
        status=200,
    )
    return mocked_responses


@pytest.fixture
def esxi_authed(mocked_responses):
    """Pre-register the ESXi /api/session POST."""
    mocked_responses.add(
        responses_lib.POST,
        "https://esxi.test/api/session",
        json="esxi-token-abc",
        status=200,
    )
    return mocked_responses


@pytest.fixture
def sddc_authed(mocked_responses):
    """Pre-register the SDDC Manager /v1/tokens POST."""
    mocked_responses.add(
        responses_lib.POST,
        "https://sm.test/v1/tokens",
        json={"accessToken": "jwt-abc", "refreshToken": {"id": "r"}},
        status=200,
    )
    return mocked_responses


@pytest.fixture
def vcf_installer_authed(mocked_responses):
    """Pre-register the VCF Installer /v1/tokens POST."""
    mocked_responses.add(
        responses_lib.POST,
        "https://installer.test/v1/tokens",
        json={"accessToken": "installer-jwt-abc"},
        status=200,
    )
    return mocked_responses


@pytest.fixture
def vcfops_authed(mocked_responses):
    """Pre-register the VCF Operations token acquire endpoint."""
    mocked_responses.add(
        responses_lib.POST,
        "https://ops.test/suite-api/api/auth/token/acquire",
        json={"token": "ops-tok-abc", "validity": 1736294400000},
        status=200,
    )
    return mocked_responses
