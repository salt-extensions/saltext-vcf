"""Tests for the ABX-rooted vcfa_* clients (action, secret, subscription, resource_action)."""

import json

import responses

from saltext.vcf.clients import vcfa_action
from saltext.vcf.clients import vcfa_action_secret
from saltext.vcf.clients import vcfa_action_subscription
from saltext.vcf.clients import vcfa_resource_action

# -- action_secret -----------------------------------------------------


def test_action_secret_list_by_project(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/abx/api/resources/action-secrets",
        json={"content": []},
        status=200,
    )
    vcfa_action_secret.list_(opts, project_id="p-1")
    assert "projects=p-1" in vcfa_authed.calls[-1].request.url


def test_action_secret_create(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/abx/api/resources/action-secrets",
        json={"id": "sec-1"},
        status=200,
    )
    vcfa_action_secret.create(opts, {"name": "s", "value": "v", "projectId": "p-1"})


def test_action_secret_update_is_put(opts, vcfa_authed):
    vcfa_authed.add(
        responses.PUT,
        "https://vcfa.test/abx/api/resources/action-secrets/sec-1",
        json={"id": "sec-1"},
        status=200,
    )
    vcfa_action_secret.update(opts, "sec-1", {"value": "new"})


# -- action ------------------------------------------------------------


def test_action_list(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/abx/api/resources/actions",
        json={"content": [{"id": "a-1"}]},
        status=200,
    )
    assert vcfa_action.list_(opts) == [{"id": "a-1"}]


def test_action_run_sends_inputs(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/abx/api/resources/actions/a-1/run",
        json={"id": "ar-1", "status": "RUNNING"},
        status=200,
    )
    out = vcfa_action.run(opts, "a-1", inputs={"k": "v"})
    assert out == {"id": "ar-1", "status": "RUNNING"}
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {"inputs": {"k": "v"}}


def test_action_list_runs(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/abx/api/resources/actions/a-1/action-runs",
        json={"content": [{"id": "ar-1"}]},
        status=200,
    )
    assert vcfa_action.list_runs(opts, "a-1") == [{"id": "ar-1"}]


# -- action_subscription ----------------------------------------------


def test_subscription_create(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/event-broker/api/subscriptions",
        json={"id": "sub-1"},
        status=200,
    )
    vcfa_action_subscription.create(
        opts,
        {
            "name": "post-provision",
            "eventTopicId": "compute.provision.post",
            "runnableType": "extensibility.abx",
            "runnableId": "a-1",
        },
    )


def test_subscription_list_event_topics(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/event-broker/api/event-topics",
        json={"content": [{"id": "compute.provision.post"}]},
        status=200,
    )
    out = vcfa_action_subscription.list_event_topics(opts)
    assert out == [{"id": "compute.provision.post"}]


# -- resource_action --------------------------------------------------


def test_resource_action_create(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/form-service/api/custom/resource-actions",
        json={"id": "ra-1"},
        status=200,
    )
    vcfa_resource_action.create(
        opts,
        {
            "name": "snapshot",
            "resourceType": "Cloud.vSphere.Machine",
            "runnableType": "extensibility.abx",
            "runnableId": "a-1",
        },
    )


def test_resource_action_delete(opts, vcfa_authed):
    vcfa_authed.add(
        responses.DELETE,
        "https://vcfa.test/form-service/api/custom/resource-actions/ra-1",
        status=204,
    )
    assert vcfa_resource_action.delete(opts, "ra-1") == {}
