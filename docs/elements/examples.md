# Element Engine Examples

Here are common examples of how to interact with the Element Engine via MCP.

## 1. Extracting Text from an Element

Find the element first:
```json
{
  "name": "browser.element.find",
  "arguments": {
    "session_id": "session_123",
    "page_id": "page_456",
    "strategy": "css",
    "value": "#header-title"
  }
}
```
*Response*: `{"element_id": "element_abc", ...}`

Extract the text:
```json
{
  "name": "browser.element.text",
  "arguments": {
    "session_id": "session_123",
    "page_id": "page_456",
    "element_id": "element_abc"
  }
}
```
*Response*: `{"text": "Welcome to the Platform", ...}`

## 2. Checking Element State

Before interacting with an element, you may want to ensure it is visible and enabled.
```json
{
  "name": "browser.element.state",
  "arguments": {
    "session_id": "session_123",
    "page_id": "page_456",
    "element_id": "element_abc"
  }
}
```
*Response*:
```json
{
  "exists": true,
  "visible": true,
  "enabled": true,
  "editable": false,
  "checked": false
}
```

## 3. Finding Multiple Elements

When you want to resolve all matching elements at once.
```json
{
  "name": "browser.element.find_all",
  "arguments": {
    "session_id": "session_123",
    "page_id": "page_456",
    "strategy": "xpath",
    "value": "//tr"
  }
}
```
*Response*:
```json
{
  "count": 5,
  "elements": [
    {"element_id": "element_0", "index": 0},
    {"element_id": "element_1", "index": 1}
    ...
  ]
}
```
