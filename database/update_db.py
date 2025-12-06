import json
import argparse
import os
import sys

def update_database(input_file, db_file='db.json'):
    print(f"--- Starting Update Process ---")
    print(f"Target Database: {db_file}")
    print(f"Input Source:    {input_file}\n")

    # 1. Load the existing Database
    if os.path.exists(db_file):
        with open(db_file, 'r', encoding='utf-8') as f:
            try:
                db_data = json.load(f)
            except json.JSONDecodeError:
                print("Error: words.json is corrupted or empty. Starting with an empty list.")
                db_data = []
    else:
        print(f"Warning: {db_file} not found. Creating a new database.")
        db_data = []

    # 2. Load the Input File
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        sys.exit(1)

    with open(input_file, 'r', encoding='utf-8') as f:
        try:
            input_data = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Input file '{input_file}' is not valid JSON.")
            sys.exit(1)

    # Ensure input is a list
    if isinstance(input_data, dict):
        input_data = [input_data]

    # Create a lookup map for existing words to find them quickly
    # Map format: { "WordString": IndexInList }
    db_index_map = {item.get('word'): i for i, item in enumerate(db_data) if item.get('word')}

    # Statistics Counters
    stats = {
        "words_before": len(db_data),
        "words_added": 0,
        "words_updated": 0,  # Count of existing words that had at least one field changed
        "field_updates": {}  # Count of specific field changes
    }

    # 3. Process Input Data
    for entry in input_data:
        word_key = entry.get('word')

        if not word_key:
            continue  # Skip entries without a 'word' field

        if word_key in db_index_map:
            # --- Logic for Existing Word ---
            idx = db_index_map[word_key]
            existing_entry = db_data[idx]
            entry_was_updated = False

            for field, new_value in entry.items():
                # Skip the identifier field
                if field == 'word':
                    continue

                # RULE 1: If field is not null, rewrite it
                if new_value is not None:
                    current_value = existing_entry.get(field)

                    # Only count/write if the value is actually different
                    if current_value != new_value:
                        existing_entry[field] = new_value

                        # Update stats
                        stats["field_updates"][field] = stats["field_updates"].get(field, 0) + 1
                        entry_was_updated = True

            if entry_was_updated:
                stats["words_updated"] += 1

        else:
            # --- Logic for New Word ---
            # RULE: Add the complete row
            db_data.append(entry)
            # Add to map in case valid duplicates exist in the input file sequence
            db_index_map[word_key] = len(db_data) - 1
            stats["words_added"] += 1

    # 4. Save the updated Database
    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, indent=2, ensure_ascii=False)

    # 5. Print Report
    print("--- Update Report ---")
    print(f"Words (Before): {stats['words_before']}")
    print(f"Words (After):  {len(db_data)}")
    print(f"Words Added:    {stats['words_added']}")
    print(f"Words Updated:  {stats['words_updated']}")

    print("\nField Update Breakdown:")
    if stats["field_updates"]:
        for field, count in stats["field_updates"].items():
            print(f"  - '{field}': updated {count} times")
    else:
        print("  (No existing fields were modified)")

    print("\nSuccess! Database saved.")


if __name__ == "__main__":
    input_file_main = 'database/update_to_db.json'
    main_db_file_name = 'database/db.json'

    update_database(input_file=input_file_main, db_file=main_db_file_name)