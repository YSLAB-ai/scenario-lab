from forecasting_harness.domain.template_utils import term_match_score


def test_term_match_score_matches_adjectival_forms_without_short_token_false_positives() -> None:
    text = "Chinese and Japanese officials keep emergency backchannel talks open to avoid a wider clash in the strait."

    assert term_match_score(text, "Japan") > 0
    assert term_match_score(text, "China") > 0
    assert term_match_score(text, "India") == 0
    assert term_match_score(text, "Pakistan") == 0
