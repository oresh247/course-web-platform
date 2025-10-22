# JSON Parsing Improvements for AI Content Generation

## Overview
This document describes the improvements made to handle JSON parsing errors when generating course content using OpenAI API.

## Problem
The OpenAI API sometimes returns invalid JSON with syntax errors such as:
- Missing commas between elements
- Trailing commas before closing brackets
- Truncated responses due to max_tokens limit
- Double commas
- Missing quotes closure

## Solutions Implemented

### 1. Increased Token Limits
**Location:** `backend/ai/content_generator.py`

- **Module content generation**: 4000 → 8000 tokens
- **Lesson content generation**: 3000 → 6000 tokens  
- **Topic material generation**: 4000 → 6000 tokens

**Rationale:** Russian text with detailed educational content requires more tokens than English. The original limits were too restrictive, causing response truncation.

### 2. Enhanced JSON Error Detection

#### Truncation Detection
- Check `finish_reason` field from OpenAI response
- If `finish_reason == "length"`, log a warning about truncation
- Automatically attempt to close truncated JSON

#### Better Error Context
- Show 100 characters before and after error position (was 50)
- Save both original and fixed JSON to debug files for analysis
- Include error details in debug files

### 3. Improved JSON Auto-Repair

#### New Repair Techniques (`_fix_json_errors` method):

1. **Trailing commas removal**
   ```json
   // Before: {"items": [1, 2,]}
   // After:  {"items": [1, 2]}
   ```

2. **Double commas fix**
   ```json
   // Before: {"a": 1,, "b": 2}
   // After:  {"a": 1, "b": 2}
   ```

3. **Missing commas between strings**
   ```json
   // Before: "text1"
   //         "text2"
   // After:  "text1",
   //         "text2"
   ```

4. **Missing commas between objects**
   ```json
   // Before: {...}
   //         {...}
   // After:  {...},
   //         {...}
   ```

5. **Missing commas after closing brackets**
   ```json
   // Before: }
   //         "field"
   // After:  },
   //         "field"
   ```

6. **Context-aware comma insertion**
   - If error position indicates missing comma, insert it at the exact position

### 4. Truncated JSON Recovery

**New method:** `_attempt_close_json`

When JSON is truncated:
1. Count open/close braces `{}` and brackets `[]`
2. Check for unclosed strings (odd number of quotes)
3. Close unclosed string if needed
4. Remove trailing comma if present
5. Add missing closing brackets `]`
6. Add missing closing braces `}`

**Example:**
```json
// Truncated input:
{
  "lectures": [
    {
      "title": "Intro",
      "slides": [
        {"slide": 1, "content": "text

// Auto-completed output:
{
  "lectures": [
    {
      "title": "Intro",
      "slides": [
        {"slide": 1, "content": "text"}
      ]
    }
  ]
}
```

### 5. Enhanced Debugging

#### Debug File Format
Files saved to `debug_json/failed_json_YYYYMMDD_HHMMSS.txt` with:
- Error message and details
- Original JSON (as received from API)
- Fixed JSON (after repair attempts)
- Clear separators for easy analysis

#### Logging Improvements
- Added emoji indicators for different states: ✅ 🔧 ⚠️ ❌ 💾
- Log finish_reason to detect truncation early
- Log JSON length and structure info
- More detailed error context

### 6. Flexible JSON Structure Validation

**Updated:** `_extract_json` method now accepts `expected_key` parameter

```python
# For module content (expects "lectures" key)
json_content = self._extract_json(content, expected_key="lectures")

# For topic material (flexible structure)
json_content = self._extract_json(content, expected_key=None)
```

Benefits:
- Less strict validation when appropriate
- Still validates critical structures
- Logs warnings instead of failing completely

## Testing & Monitoring

### Success Indicators
From logs, you should see:
```
✅ Получена правильная структура с 'lectures'
✅ JSON mode успешно: X лекций, Y слайдов
✅ Контент урока сгенерирован: X слайдов
```

### Warning Indicators
```
⚠️ Ответ был обрезан из-за лимита токенов!
⚠️ JSON выглядит обрезанным
⚠️ Отсутствует ожидаемый ключ 'lectures'
```

### Error Indicators
```
❌ Не удалось исправить JSON
❌ JSON mode не сработал
💾 Проблемный JSON сохранен в: debug_json/...
```

## Future Improvements

1. **Chunked Generation**: If a module has many lessons, split generation into multiple API calls
2. **Retry with Reduced Scope**: On failure, try generating fewer slides per lecture
3. **JSON Schema Validation**: Use OpenAI's structured outputs with JSON schema
4. **Streaming Parsing**: Parse JSON incrementally to detect errors early
5. **LLM-based Repair**: Use a separate API call to fix malformed JSON

## Related Files

- `backend/ai/content_generator.py` - Main implementation
- `backend/ai/prompts.py` - Prompts for content generation
- `backend/ai/openai_client.py` - OpenAI API client
- `backend/models/domain.py` - Data models for content

## Common Issues

### Issue: "Expecting ',' delimiter"
**Cause:** AI forgot to add comma between elements
**Fix:** Auto-repair patterns #3, #4, #5

### Issue: "Unterminated string"
**Cause:** Response truncated mid-string
**Fix:** `_attempt_close_json` closes the string and structure

### Issue: "Extra data after JSON"
**Cause:** AI added comments or text after JSON
**Fix:** Extract JSON block between first `{` and last `}`

### Issue: finish_reason = "length"
**Cause:** max_tokens limit reached
**Fix:** 
1. Increased token limits (already done)
2. If still happening, reduce number of lessons per generation
3. Or increase max_tokens further (balance cost vs quality)

## Performance Notes

- Average response time: 30-90 seconds per module generation
- Token usage: ~6000-8000 tokens for Russian detailed content
- Success rate after improvements: Expected >95%
- Fallback strategy: Test content generation if all methods fail

## Configuration

Current settings in `content_generator.py`:

```python
# Module content generation
model="gpt-4-turbo-preview"
temperature=0.3
max_tokens=8000
response_format={"type": "json_object"}

# Lesson content generation  
model="gpt-4-turbo-preview"
temperature=0.3
max_tokens=6000
response_format={"type": "json_object"}

# Topic material generation
model="gpt-4-turbo-preview"  
temperature=0.7
max_tokens=6000
response_format={"type": "json_object"}
```

## Rollback Instructions

If these changes cause issues, you can:

1. Revert max_tokens to original values (4000, 3000, 4000)
2. Remove `_attempt_close_json` calls
3. Revert `_fix_json_errors` to simple version
4. Remove `expected_key` parameter from `_extract_json`

However, this will bring back the original JSON parsing errors.

