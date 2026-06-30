# API Reference

## `GET /health`

Returns service health.

## `GET /v1/models`

Lists available demo models.

## `GET /v1/tenant/usage`

Returns usage records for the authenticated tenant.

Requires:

```http
Authorization: Bearer demo-key-acme
```

## `POST /v1/chat/completions`

Creates a mock chat completion through the gateway.

Requires:

```http
Authorization: Bearer demo-key-acme
Content-Type: application/json
```

Body:

```json
{
  "model": "auto",
  "task_type": "summarization",
  "messages": [
    {
      "role": "user",
      "content": "Summarize this text."
    }
  ],
  "metadata": {
    "user_id": "demo-user"
  }
}
```
