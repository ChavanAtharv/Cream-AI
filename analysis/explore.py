"""Print three facts about the SchemeSaathi records using pandas.

Run from the project root:
    python -m analysis.explore
"""

import pandas as pd

from app.records import load_records


def build_dataframe():
    """Load records into a DataFrame with a document-count column."""
    frame = pd.DataFrame(load_records())
    frame["document_count"] = frame["documents_required"].apply(
        lambda docs: len(docs) if isinstance(docs, list) else 0
    )
    return frame


def main():
    frame = build_dataframe()

    # Fact 1: dataset size and category spread.
    by_category = frame["category"].value_counts()
    print(f"Fact 1: {len(frame)} schemes across {by_category.size} categories.")
    print(f"        Largest category: {by_category.index[0]} "
          f"({by_category.iloc[0]} schemes).")

    # Fact 2: which scheme asks for the most documents.
    top = frame.loc[frame["document_count"].idxmax()]
    print(f"Fact 2: '{top['scheme_name']}' lists the most documents "
          f"({top['document_count']}); average is "
          f"{frame['document_count'].mean():.1f}.")

    # Fact 3: schemes with no documents listed.
    empty = frame[frame["document_count"] == 0]["scheme_name"].tolist()
    print(f"Fact 3: {len(empty)} scheme(s) list no documents: "
          f"{', '.join(empty) if empty else 'none'}.")


if __name__ == "__main__":
    main()
