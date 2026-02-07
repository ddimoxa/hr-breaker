from hr_breaker.openai_keys import get_openai_api_keys, mask_key


def test_get_openai_api_keys_parses_numbered_then_list_then_single():
    env = {
        "OPENAI_API_KEY_2": "k2",
        "OPENAI_API_KEY_1": "k1",
        "OPENAI_API_KEYS": "k3, k4\nk5",
        "OPENAI_API_KEY": "k6",
    }
    assert get_openai_api_keys(env) == ["k1", "k2", "k3", "k4", "k5", "k6"]


def test_get_openai_api_keys_dedupes_preserving_first_occurrence():
    env = {
        "OPENAI_API_KEY_1": "k1",
        "OPENAI_API_KEYS": "k1,k2",
        "OPENAI_API_KEY": "k2",
    }
    assert get_openai_api_keys(env) == ["k1", "k2"]


def test_mask_key_does_not_leak_full_secret():
    assert mask_key("sk-test-1234567890") != "sk-test-1234567890"
    assert mask_key("short") == "*****"

