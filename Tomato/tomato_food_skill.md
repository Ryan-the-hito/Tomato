---
name: tomato-food-log
description: Use when the user tells you what they ate or drank ("午饭吃了咖喱饭", "I had two eggs for breakfast", "今日の昼はラーメン"), or gives you the nutrition facts of a food (a photo of the label, pasted text, a table) to keep, and the Tomato tools are available. NOT for recipes to cook, diet advice, or questions that only ask about nutrition without wanting anything recorded.
---

# Meals and foods through Tomato

Tomato is the app on this Mac that keeps the user's day: a diary with one line per event, and Collections — tables
the user fills, one of them usually for food (dishes with their nutrition). You reach it through the Tomato tools
(`list_collections`, `search_collection`, `read_collection_row`, `create_collection_row`, `update_collection_row`,
`write_diary_line`, `read_diary`). If those tools are not offered to you, say that Tomato is not connected and stop.

Two different things are kept in two places — do not mix them:
- **What a food is** (its name, calories, protein …) → a row of the food collection. Written once, reused.
- **That the user ate it** (today, at this time, how much) → one line in the diary, pointing at that row.
  Never add a row to the collection just because something was eaten again.

## When the user says what they ate

1. `list_collections`, and pick the collection that holds foods (by its name and columns). None looks like food:
   ask the user which one to use, or whether to make one (`create_collection` with columns such as Dish, Calories,
   Protein (g), Fat (g), Carbs (g), Notes — only after a yes).
2. `search_collection` for each food, with one or two key words (try the user's wording first, then a shorter or
   translated one).
3. **Found** → `write_diary_line` with `collection`, the `row` number, and a `note` for the amount or anything said
   about it ("half a portion", "×2"). Pass `time` ("HH:MM") when the user said when it was, or when it clearly was
   not just now ("at lunch" told in the evening → ask or use what they said; do not guess a time).
4. **Not found** → say so, and ask whether to add it to the collection. Yes: `create_collection_row` with what you
   know (the name; nutrition only if the user gave it or asks you to look it up — then say where the numbers are
   from), then step 3 with the new row. No: `write_diary_line` with plain `text` ("ate: …").
5. Several foods in one meal: one diary line each, same `time`.
6. Tell the user in one or two lines what was written. Do not label the meal (breakfast / lunch …): the line carries
   the time, and Tomato's daily report sorts meals by it.

## When the user gives nutrition facts (photo, pasted text, table)

1. Read the numbers and show them back as a small table: per which amount (100 g / one serving / the whole pack),
   then each nutrient with its unit. Say plainly what you could not read; never fill a gap with a typical value.
2. Find the food's row (`search_collection`). Not there → ask whether to add it.
3. Match the nutrients to the collection's columns. Write numbers only, the unit belongs to the column's name
   (Calories → `650`, not `650 kcal`), so that Tomato can add them up.
4. A nutrient that has no column: list those and ask whether to add the columns. Only after a yes, pass
   `add_missing_columns: true` with clear names that include the unit ("Protein (g)", "Sodium (mg)").
5. `update_collection_row` (or `create_collection_row`). Cells you do not pass stay as they are; never empty a cell
   the user filled unless they ask.
6. If the per-amount basis is not what the collection uses elsewhere (per 100 g vs per serving), ask which to store
   rather than converting silently; put the basis in a Notes column when there is one.

## Limits

- Change only what the user asked for. Deleting rows or collections is not part of this skill.
- Tomato may answer that it "is in the middle of an edit": the user is typing in it. Wait a moment and try once more,
  then tell the user.
