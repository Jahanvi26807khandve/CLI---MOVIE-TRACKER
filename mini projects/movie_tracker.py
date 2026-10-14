"""
Movie Tracker - a menu-driven CLI application (CRUD + statistics).
Data is stored in a JSON file called movies.json.
"""

import json
import os

# movies.json is stored in the same folder as this script
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.json")

STATUS_OPTIONS = ["Plan to Watch", "Watching", "Completed"]
TYPE_OPTIONS = ["Movie", "Series"]


# =====================================================
# FILE HANDLING (load and save JSON)
# =====================================================

def start_fresh_after_bad_file():
    """Called when movies.json is damaged: keep a copy and start with an empty list."""
    backup_name = DATA_FILE + ".corrupt"
    try:
        os.replace(DATA_FILE, backup_name)
        print(f"Warning: movies.json was damaged. A copy was kept as '{backup_name}'.")
    except OSError:
        print("Warning: movies.json was damaged and could not be backed up.")
    print("Starting with an empty list.")
    save_titles([])
    return []


def load_titles():
    """Read all titles from movies.json. Create the file if it does not exist."""
    if not os.path.exists(DATA_FILE):
        save_titles([])
        print("No data file found, so a new movies.json was created.")
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        return start_fresh_after_bad_file()
    except OSError as error:
        print(f"Could not read movies.json: {error}")
        return []

    # The file must contain a list of records
    if not isinstance(data, list):
        return start_fresh_after_bad_file()
    return data


def save_titles(titles):
    """Write all titles to movies.json. Returns True if saving worked."""
    temp_file = DATA_FILE + ".tmp"
    try:
        # Write to a temporary file first, then replace the real file.
        # This way a crash in the middle of writing cannot ruin movies.json.
        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump(titles, file, indent=4)
        os.replace(temp_file, DATA_FILE)
        return True
    except OSError as error:
        print(f"Error: could not save data: {error}")
        return False


# =====================================================
# INPUT HELPERS (every one of them keeps asking until the input is valid)
# =====================================================

def ask_text(prompt, required=False):
    """Ask for text. If required, an empty answer is not accepted."""
    while True:
        value = input(prompt).strip()
        if value or not required:
            return value
        print("This field cannot be empty.")


def ask_int(prompt, min_value, max_value=None, optional=False):
    """Ask for a whole number within limits. If optional, Enter returns None."""
    while True:
        text = input(prompt).strip()
        if text == "" and optional:
            return None
        try:
            number = int(text)
        except ValueError:
            print("Please enter a whole number (for example 120).")
            continue
        if number < min_value:
            print(f"The number must be at least {min_value}.")
            continue
        if max_value is not None and number > max_value:
            print(f"The number must not be more than {max_value}.")
            continue
        return number


def ask_rating(prompt):
    """Ask for a rating from 0 to 10. Enter returns None (no rating)."""
    while True:
        text = input(prompt).strip()
        if text == "":
            return None
        try:
            rating = float(text)
        except ValueError:
            print("Please enter a number such as 8 or 7.5.")
            continue
        if not (0 <= rating <= 10):
            print("Rating must be between 0 and 10.")
            continue
        return round(rating, 1)


def ask_choice(heading, options):
    """Show a numbered list and return the option the user picked."""
    print(heading)
    for number, option in enumerate(options, start=1):
        print(f"  {number}. {option}")
    picked = ask_int("Enter choice number: ", 1, len(options))
    return options[picked - 1]


def ask_yes_no(prompt):
    """Ask a yes/no question. Returns True for yes, False for no."""
    while True:
        answer = input(prompt + " (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please type y or n.")


# =====================================================
# CALCULATION AND DISPLAY HELPERS
# =====================================================

def format_minutes(minutes):
    """Turn 150 into '150 minutes (about 2.5 hours)'."""
    return f"{minutes} minutes (about {minutes / 60:.1f} hours)"


def show_value(value):
    """Show 'N/A' for empty optional values."""
    if value is None or value == "":
        return "N/A"
    return value


def total_runtime(item):
    """Total runtime of a whole title in minutes."""
    if item["type"] == "Movie":
        return item["runtime_minutes"]
    return item["total_episodes"] * item["episode_duration"]


def remaining_minutes(item):
    """Estimated minutes still to watch (0 if the title is Completed)."""
    if item["status"] == "Completed":
        return 0
    if item["type"] == "Movie":
        return item["runtime_minutes"]
    episodes_left = item["total_episodes"] - item["episodes_watched"]
    return episodes_left * item["episode_duration"]


def display_title(item, number=None):
    """Print one title in a neat block."""
    print("-" * 45)
    heading = item["title"]
    if number is not None:
        heading = f"{number}. {heading}"
    print(heading)
    print(f"   Type    : {item['type']}")
    print(f"   Year    : {show_value(item.get('year'))}")
    print(f"   Genre   : {show_value(item.get('genre'))}")
    print(f"   Status  : {item['status']}")

    rating = item.get("rating")
    print(f"   Rating  : {str(rating) + '/10' if rating is not None else 'N/A'}")
    print(f"   Notes   : {show_value(item.get('notes'))}")

    if item["type"] == "Movie":
        print(f"   Runtime : {format_minutes(item['runtime_minutes'])}")
    else:
        watched = item["episodes_watched"]
        total = item["total_episodes"]
        percent = watched / total * 100
        print(f"   Seasons : {show_value(item.get('seasons'))}")
        print(f"   Episodes: {watched}/{total} watched ({percent:.1f}%)")
        print(f"   Episode length: {item['episode_duration']} minutes (average)")


def show_series_progress(item):
    """Print the detailed progress report for a series."""
    watched = item["episodes_watched"]
    total = item["total_episodes"]
    remaining = total - watched
    percent = watched / total * 100
    time_left = remaining * item["episode_duration"]

    print(f"\nProgress for: {item['title']}")
    print(f"  Episodes watched : {watched} / {total}")
    print(f"  Episodes remaining: {remaining}")
    print(f"  Percentage completed: {percent:.1f}%")
    print(f"  Estimated time left : {format_minutes(time_left)}")
    print(f"  Current status      : {item['status']}")


def auto_update_status(item):
    """Set a series status automatically from its episode count."""
    watched = item["episodes_watched"]
    total = item["total_episodes"]
    if watched == total:
        new_status = "Completed"
    elif watched > 0:
        new_status = "Watching"
    else:
        new_status = "Plan to Watch"

    if new_status != item["status"]:
        print(f"Status automatically changed from '{item['status']}' to '{new_status}'.")
        item["status"] = new_status


# =====================================================
# SEARCH HELPERS
# =====================================================

def find_by_title(titles, name):
    """Return the record whose title matches exactly (ignoring case), else None."""
    for item in titles:
        if item["title"].lower() == name.lower():
            return item
    return None


def search_matches(titles, text):
    """Return every record whose title contains the text (ignoring case)."""
    matches = []
    for item in titles:
        if text.lower() in item["title"].lower():
            matches.append(item)
    return matches


def select_title(titles, only_type=None):
    """Ask the user to search for a title and pick one. Returns a record or None."""
    # Build the pool of titles we are allowed to choose from
    pool = []
    for item in titles:
        if only_type is None or item["type"] == only_type:
            pool.append(item)

    if not pool:
        if only_type is None:
            print("Your list is empty.")
        else:
            print(f"You have no saved titles of type '{only_type}'.")
        return None

    text = ask_text("Enter the title (or part of it): ", required=True)
    matches = search_matches(pool, text)

    if not matches:
        print(f"No title found matching '{text}'.")
        return None

    # If exactly one title matches the full name, use it straight away
    exact = [item for item in matches if item["title"].lower() == text.lower()]
    if len(exact) == 1:
        return exact[0]

    if len(matches) == 1:
        print(f"Found: {matches[0]['title']}")
        return matches[0]

    print(f"\nFound {len(matches)} matches:")
    for number, item in enumerate(matches, start=1):
        print(f"  {number}. {item['title']} ({item['type']}, {show_value(item.get('year'))})")
    picked = ask_int("Choose a number (0 to cancel): ", 0, len(matches))
    if picked == 0:
        return None
    return matches[picked - 1]


# =====================================================
# MAIN FEATURES
# =====================================================

def add_title(titles):
    """A. Add a new movie or series."""
    print("\n--- Add a Movie or Series ---")
    name = ask_text("Title name: ", required=True)

    # Duplicate check (case-insensitive)
    while find_by_title(titles, name) is not None:
        print(f"\n'{name}' is already in your list.")
        choice = ask_choice("What would you like to do?",
                            ["Enter a different title", "Add it anyway", "Cancel"])
        if choice == "Enter a different title":
            name = ask_text("New title name: ", required=True)
        elif choice == "Add it anyway":
            break
        else:
            print("Cancelled. Nothing was added.")
            return

    title_type = ask_choice("\nType:", TYPE_OPTIONS)
    year = ask_int("Release year (optional, press Enter to skip): ", 1888, 2100, optional=True)
    genre = ask_text("Genre (optional): ")
    status = ask_choice("\nWatch status:", STATUS_OPTIONS)
    rating = ask_rating("Personal rating out of 10 (optional): ")
    notes = ask_text("Notes (optional): ")

    record = {
        "title": name,
        "type": title_type,
        "year": year,
        "genre": genre,
        "status": status,
        "rating": rating,
        "notes": notes,
    }

    if title_type == "Movie":
        record["runtime_minutes"] = ask_int("Runtime in minutes: ", 1)
    else:
        total = ask_int("Total number of episodes: ", 1)
        seasons = ask_int("Number of seasons (optional, press Enter to skip): ", 1, optional=True)
        duration = ask_int("Average duration per episode in minutes: ", 1)

        # Decide how many episodes were watched, based on the chosen status
        if status == "Completed":
            watched = total
            print("Status is Completed, so episodes watched was set to the total.")
        elif status == "Plan to Watch":
            watched = 0
        else:  # Watching
            watched = ask_int(f"Episodes watched so far (0 to {total}): ", 0, total)
            if watched == total:
                record["status"] = "Completed"
                print("All episodes watched, so status was set to Completed.")

        record["total_episodes"] = total
        record["episodes_watched"] = watched
        record["episode_duration"] = duration
        record["seasons"] = seasons

    titles.append(record)
    print(f"\nSaved: '{name}' was added to your list.")


def view_all(titles):
    """B. Show every saved title."""
    print("\n========== ALL TITLES ==========")
    if not titles:
        print("Your list is empty. Choose option 1 to add your first movie or series.")
        return
    for number, item in enumerate(titles, start=1):
        display_title(item, number)
    print("-" * 45)
    print(f"Total: {len(titles)} title(s)")


def search_title(titles):
    """F. Case-insensitive search by title."""
    print("\n--- Search for a Title ---")
    if not titles:
        print("Your list is empty, so there is nothing to search.")
        return
    text = ask_text("Enter the title (or part of it): ", required=True)
    matches = search_matches(titles, text)
    if not matches:
        print(f"No title found matching '{text}'. Try a shorter search word.")
        return
    print(f"\nFound {len(matches)} match(es):")
    for item in matches:
        display_title(item)
    print("-" * 45)


def update_episode_progress(titles):
    """C. Update how many episodes of a series have been watched."""
    print("\n--- Update Series Episode Progress ---")
    item = select_title(titles, only_type="Series")
    if item is None:
        return

    show_series_progress(item)
    total = item["total_episodes"]
    new_watched = ask_int(f"\nNew number of episodes watched (0 to {total}): ", 0, total)
    item["episodes_watched"] = new_watched
    auto_update_status(item)
    show_series_progress(item)
    print("\nTip: you can change the status manually using 'Update a Title'.")


def change_status(item):
    """Manually change the watch status."""
    new_status = ask_choice("Choose the new status:", STATUS_OPTIONS)
    item["status"] = new_status
    # A Completed series must have all episodes watched
    if (item["type"] == "Series" and new_status == "Completed"
            and item["episodes_watched"] < item["total_episodes"]):
        item["episodes_watched"] = item["total_episodes"]
        print("Episodes watched was set to the total because the series is Completed.")
    print(f"Status is now: {new_status}")


def update_series_details(item):
    """Change total episodes, episode length and seasons of a series."""
    watched = item["episodes_watched"]
    minimum = max(1, watched)
    item["total_episodes"] = ask_int(
        f"Total episodes (now {item['total_episodes']}, minimum {minimum}): ", minimum)
    item["episode_duration"] = ask_int(
        f"Average episode duration in minutes (now {item['episode_duration']}): ", 1)
    item["seasons"] = ask_int("Number of seasons (press Enter to leave empty): ", 1, optional=True)
    auto_update_status(item)
    print("Series details updated.")


def update_title(titles):
    """D. Search for a title and update one of its details."""
    print("\n--- Update a Title ---")
    item = select_title(titles)
    if item is None:
        return

    display_title(item)

    options = ["Watch status", "Personal rating", "Notes", "Release year", "Genre"]
    if item["type"] == "Movie":
        options.append("Runtime")
    else:
        options.append("Episode progress")
        options.append("Series details (total episodes, episode length, seasons)")
    options.append("Cancel")

    choice = ask_choice("\nWhat do you want to update?", options)

    if choice == "Watch status":
        change_status(item)
    elif choice == "Personal rating":
        item["rating"] = ask_rating("New rating out of 10 (press Enter to remove): ")
        print("Rating updated.")
    elif choice == "Notes":
        item["notes"] = ask_text("New notes (press Enter to clear): ")
        print("Notes updated.")
    elif choice == "Release year":
        item["year"] = ask_int("New release year (press Enter to clear): ", 1888, 2100, optional=True)
        print("Release year updated.")
    elif choice == "Genre":
        item["genre"] = ask_text("New genre (press Enter to clear): ")
        print("Genre updated.")
    elif choice == "Runtime":
        item["runtime_minutes"] = ask_int("New runtime in minutes: ", 1)
        print("Runtime updated.")
    elif choice == "Episode progress":
        total = item["total_episodes"]
        item["episodes_watched"] = ask_int(
            f"New number of episodes watched (0 to {total}): ", 0, total)
        auto_update_status(item)
        print("Episode progress updated.")
    elif choice.startswith("Series details"):
        update_series_details(item)
    else:
        print("Cancelled. Nothing was changed.")


def delete_title(titles):
    """E. Search for a title and delete it after confirmation."""
    print("\n--- Delete a Title ---")
    item = select_title(titles)
    if item is None:
        return
    display_title(item)
    if ask_yes_no(f"\nDelete '{item['title']}' permanently?"):
        titles.remove(item)
        print("Deleted.")
    else:
        print("Cancelled. Nothing was deleted.")


def print_stat(label, value, explanation):
    """Print one statistic with a short explanation under it."""
    print(f"\n{label}: {value}")
    print(f"   ({explanation})")


def show_statistics(titles):
    """G. Show watch-time statistics."""
    print("\n========== WATCH-TIME STATISTICS ==========")
    if not titles:
        print("No titles saved yet, so there are no statistics to show.")
        return

    movie_count = 0
    series_count = 0
    completed_count = 0
    watching_count = 0
    completed_movie_minutes = 0
    completed_series_minutes = 0
    partial_series_minutes = 0
    episodes_watched_total = 0
    remaining_total = 0

    for item in titles:
        if item["type"] == "Movie":
            movie_count += 1
        else:
            series_count += 1

        if item["status"] == "Completed":
            completed_count += 1
            if item["type"] == "Movie":
                completed_movie_minutes += item["runtime_minutes"]
            else:
                completed_series_minutes += total_runtime(item)
        elif item["status"] == "Watching":
            watching_count += 1

        if item["type"] == "Series":
            episodes_watched_total += item["episodes_watched"]
            # Only the episodes actually watched count for unfinished series
            if item["status"] != "Completed":
                partial_series_minutes += item["episodes_watched"] * item["episode_duration"]

        remaining_total += remaining_minutes(item)

    print_stat("Total saved titles", len(titles), "all movies and series in your list")
    print_stat("Movies", movie_count, "titles of type Movie")
    print_stat("Series", series_count, "titles of type Series")
    print_stat("Completed titles", completed_count, "titles with status Completed")
    print_stat("Currently watching", watching_count, "titles with status Watching")
    print_stat("Watch time of completed movies", format_minutes(completed_movie_minutes),
               "sum of runtimes of movies marked Completed")
    print_stat("Watch time of completed series", format_minutes(completed_series_minutes),
               "total episodes x average episode length, only for series marked Completed")
    print_stat("Watch time of unfinished series so far", format_minutes(partial_series_minutes),
               "episodes watched x episode length, for series not yet Completed")
    print_stat("Total episodes watched", episodes_watched_total,
               "episodes watched across all series")
    print_stat("Remaining watch time", format_minutes(remaining_total),
               "full runtime of unfinished movies + unwatched episodes of unfinished series")


# =====================================================
# MENU AND PROGRAM START
# =====================================================

def show_menu():
    print("\n========== MY MOVIE TRACKER ==========")
    print("1. Add a Movie or Series")
    print("2. View All Titles")
    print("3. Search for a Title")
    print("4. Update a Title")
    print("5. Update Series Episode Progress")
    print("6. Delete a Title")
    print("7. View Watch-Time Statistics")
    print("8. Exit")


def main():
    titles = load_titles()

    while True:
        show_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_title(titles)
            save_titles(titles)
        elif choice == "2":
            view_all(titles)
        elif choice == "3":
            search_title(titles)
        elif choice == "4":
            update_title(titles)
            save_titles(titles)
        elif choice == "5":
            update_episode_progress(titles)
            save_titles(titles)
        elif choice == "6":
            delete_title(titles)
            save_titles(titles)
        elif choice == "7":
            show_statistics(titles)
        elif choice == "8":
            save_titles(titles)
            print("Your data is saved. Goodbye!")
            break
        else:
            print("Invalid option. Please enter a number from 1 to 8.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        # Data is saved after every change, so nothing is lost here
        print("\nProgram stopped. Your saved data is safe. Goodbye!")