from forecasting_harness.knowledge.manifests import DomainManifest, load_domain_manifest


def load_builtin_replay_cases():
    from forecasting_harness.knowledge.replays import load_builtin_replay_cases as _load_builtin_replay_cases

    return _load_builtin_replay_cases()


def summarize_builtin_replay_corpus():
    from forecasting_harness.knowledge.replays import summarize_builtin_replay_corpus as _summarize_builtin_replay_corpus

    return _summarize_builtin_replay_corpus()


__all__ = ["DomainManifest", "load_builtin_replay_cases", "load_domain_manifest", "summarize_builtin_replay_corpus"]
