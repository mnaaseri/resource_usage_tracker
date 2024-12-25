from unittest.mock import patch, MagicMock
import pytest
from apps.notifier_app import NotifierApp
from notifier.send_email_notification import EmailSender

import re

def normalize_whitespace(text):
    return re.sub(r'\s+', ' ', text.strip())

@pytest.fixture
def mock_email_sender():
    return MagicMock(spec=EmailSender)

@pytest.fixture
def notifier_app(mock_email_sender):
    return NotifierApp(email_sender=mock_email_sender)

def test_total_resource_usage_memory_alert(notifier_app, mock_email_sender):
    notifier_app.memory_info.get_total_memory_usage = MagicMock(
        return_value={"memory_percent": 95}
    )

    notifier_app.total_resource_usage()

    # Normalize whitespace for both expected and actual body
    expected_body = """
    Your total memory usage is 95,
    which is more that your specified threshold.
    """

    actual_body = mock_email_sender.send_email.call_args.kwargs['body']

    assert normalize_whitespace(actual_body) == normalize_whitespace(expected_body)
