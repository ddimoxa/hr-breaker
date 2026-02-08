from pydantic_ai.exceptions import ModelHTTPError

from hr_breaker.openai_rotating_model import _is_retryable_openai_http_error


def test_retryable_on_common_status_codes():
    assert _is_retryable_openai_http_error(
        ModelHTTPError(status_code=401, model_name="x", body={})
    )
    assert _is_retryable_openai_http_error(
        ModelHTTPError(status_code=403, model_name="x", body={})
    )
    assert _is_retryable_openai_http_error(
        ModelHTTPError(status_code=429, model_name="x", body={})
    )


def test_retryable_on_billing_not_active_code():
    assert _is_retryable_openai_http_error(
        ModelHTTPError(
            status_code=400,
            model_name="x",
            body={"code": "billing_not_active", "message": "Your account is not active"},
        )
    )


def test_not_retryable_on_other_client_errors():
    assert not _is_retryable_openai_http_error(
        ModelHTTPError(
            status_code=400,
            model_name="x",
            body={"code": "some_other_error", "message": "Bad request"},
        )
    )

