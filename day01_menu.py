while True:
    print("\n========== SchemeSaathi ==========")
    print("1. About SchemeSaathi")
    print("2. Sample Questions")
    print("3. Sample Eligibility Check")
    print("0. Exit")

    choice = input("\nEnter your choice: ")

    if choice == "1":
        print("\nSchemeSaathi helps people discover government schemes.")

    elif choice == "2":
        print("\nSample Questions:")
        print("1. What scholarships are available for students?")
        print("2. What government benefits are available for farmers?")

    elif choice == "3":
        age = int(input("\nEnter your age: "))

        if age >= 18:
            print("You meet this sample age condition.")
        elif age < 18:
            print("You do not meet this sample age condition.")

    elif choice == "0":
        print("\nThank you for using SchemeSaathi!")
        break

    else:
        print("\nInvalid choice. Please try again.")