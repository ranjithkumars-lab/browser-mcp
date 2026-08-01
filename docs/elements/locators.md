# Locator Strategies

The Element Engine supports the following locator strategies, passed in the `strategy` field.

## `css`
Find elements using standard CSS selectors.
```json
{"strategy": "css", "value": "button.submit"}
```

## `xpath`
Find elements using XPath expressions.
```json
{"strategy": "xpath", "value": "//div[@id='content']"}
```

## `aria`
Find elements using accessibility roles and names. Format: `role` or `role:Name`.
```json
{"strategy": "aria", "value": "button:Submit"}
{"strategy": "aria", "value": "dialog"}
```

## `text`
Find elements containing specific visible text.
```json
{"strategy": "text", "value": "Click me!"}
```

## `playwright`
A raw Playwright selector, useful for advanced Playwright-specific combinators.
```json
{"strategy": "playwright", "value": "text='Submit' >> visible=true"}
```

## Strict Mode
By default, all queries are `strict=true` meaning the locator *must* match exactly one element on the page. If it matches multiple, it throws an error. Set `strict=false` to use the first matching element instead.

## Timeouts
The `timeout` parameter allows overriding the global interaction timeout (default 5000ms) for a specific query.
