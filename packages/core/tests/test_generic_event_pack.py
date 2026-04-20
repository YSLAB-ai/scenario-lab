from forecasting_harness.domain.base import InteractionModel
from forecasting_harness.domain.generic_event import GenericEventPack


def test_generic_event_pack_defaults_to_event_driven() -> None:
    pack = GenericEventPack()

    assert pack.interaction_model() is InteractionModel.EVENT_DRIVEN
    assert pack.propose_actions(None)[0]["action_id"] == "maintain-course"
