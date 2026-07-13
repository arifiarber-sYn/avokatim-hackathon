"""WhatsApp webhook stub: handshake + Meta payload parsing (no credentials)."""
from app.api.whatsapp import extract_text_messages, whatsapp_enabled


def _meta_payload(text: str, sender: str = "38344123456") -> dict:
    """The (nested) shape Meta actually posts to the webhook."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": sender,
                                    "id": "wamid.xxx",
                                    "type": "text",
                                    "text": {"body": text},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


def test_disabled_without_credentials():
    assert whatsapp_enabled() is False


def test_extracts_text_message():
    msgs = extract_text_messages(_meta_payload("A kam të drejtë në pushim vjetor?"))
    assert msgs == [{"from": "38344123456", "text": "A kam të drejtë në pushim vjetor?"}]


def test_ignores_non_text_and_empty():
    payload = _meta_payload("ok")
    payload["entry"][0]["changes"][0]["value"]["messages"].append(
        {"from": "1", "type": "image", "image": {"id": "img1"}}
    )
    payload["entry"][0]["changes"][0]["value"]["messages"].append(
        {"from": "2", "type": "text", "text": {"body": "   "}}
    )
    msgs = extract_text_messages(payload)
    assert len(msgs) == 1 and msgs[0]["text"] == "ok"


def test_status_only_payload_yields_nothing():
    # Delivery/read receipts arrive on the same webhook without "messages"
    payload = {
        "entry": [
            {"changes": [{"value": {"statuses": [{"status": "delivered"}]}}]}
        ]
    }
    assert extract_text_messages(payload) == []
