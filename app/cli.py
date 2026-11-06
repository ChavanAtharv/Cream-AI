"""Interactive command-line interface for SchemeSaathi."""

from app.records import count_by, get_by_id, load_records, search


def display(record):
    print("\\n" + "-" * 60)
    for key in (
        "id", "scheme_name", "category", "ministry", "benefit",
        "eligibility", "documents", "source_url", "verification_status",
    ):
        value = record.get(key)
        if value is None or value == []:
            value = "Not yet documented"
        if isinstance(value, list):
            value = ", ".join(value)
        print(f"{key.replace('_', ' ').title()}: {value}")


def main():
    records = load_records()
    while True:
        print("\\n========== SchemeSaathi ==========")
        print("1. View all schemes")
        print("2. Search schemes")
        print("3. Count schemes by category")
        print("4. Find scheme by ID")
        print("0. Exit")
        choice = input("Enter choice: ").strip()

        if choice == "1":
            for record in records:
                display(record)
        elif choice == "2":
            keyword = input("Search keyword: ")
            matches = search(records, keyword)
            print(f"Found {len(matches)} result(s).")
            for record in matches:
                display(record)
        elif choice == "3":
            for category, total in count_by(records).items():
                print(f"{category}: {total}")
        elif choice == "4":
            scheme_id = input("Scheme ID: ")
            record = get_by_id(records, scheme_id)
            display(record) if record else print("Scheme ID not found.")
        elif choice == "0":
            print("Thank you for using SchemeSaathi!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
