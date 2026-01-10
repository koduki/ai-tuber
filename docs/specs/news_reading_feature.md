# News Reading Feature Specification

## Overview
This feature enables the AItuber to read a pre-prepared news script when there are no active user comments to respond to. The system prioritizes user interaction: if a comment arrives while reading, the AItuber handles the comment before resuming (or moving to the next segment).

## Data Structure (`data/news.json`)
The news data is stored in a JSON file. The structure supports categorized segments.

```json
{
  "date": "YYYY-MM-DD",
  "segments": [
    {
      "category": "weather",
      "content": "Description of the weather..."
    },
    {
      "category": "market",
      "content": "SP500: ..., Nikkei: ..., USD/JPY: ..., BTC: ..."
    },
    {
      "category": "politics_economics",
      "content": "Summary of politics and economics..."
    },
    {
      "category": "it",
      "content": "Summary of IT news..."
    }
  ]
}
```

## Logic Flow

1.  **Initialization**:
    *   `NewsManager` loads `data/news.json`.
    *   Sets `current_segment_index = 0`.

2.  **Main Loop**:
    *   **Check Comments**: Call `get_comments` tool.
    *   **If Comments Exist**:
        *   Pass comments to `SaintGraph.process_turn(comments)`.
        *   (Optional) If this interrupts a long reading, the next loop continues where it left off (or next segment). For this MVP, we assume "between segments" checks.
    *   **Else If No Comments**:
        *   Check `NewsManager.has_next()`.
        *   If `True`:
            *   Get segment: `seg = NewsManager.get_next()`.
            *   Construct Prompt: `"[Director] Next news topic: {seg.category}. Content: {seg.content}. Read this in character, adding your own perspective."`
            *   Pass to `SaintGraph.process_turn(prompt)`.
            *   `NewsManager.mark_completed()`.
        *   If `False`:
            *   Idle (wait for comments).

## Classes

### `NewsManager`
- `__init__(filepath: str)`: Loads JSON.
- `get_next_segment() -> Optional[Dict]`: Returns the next segment or None.
- `mark_completed()`: Advances the index.
- `has_next() -> bool`: Returns True if there are unread segments.
