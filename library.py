
import sqlite3

DB_NAME = "library.db"


def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE,
            category TEXT,
            available INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            borrower TEXT NOT NULL,
            issue_date TEXT DEFAULT CURRENT_TIMESTAMP,
            return_date TEXT,
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    """)

    conn.commit()
    conn.close()


def add_book():
    title = input("Enter book title: ").strip()
    author = input("Enter author name: ").strip()
    isbn = input("Enter ISBN: ").strip()
    category = input("Enter category: ").strip()

    if not title or not author:
        print("Title and author are required.")
        return

    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute(
                """INSERT INTO books
                (title, author, isbn, category)
                VALUES (?, ?, ?, ?)""",
                (title, author, isbn or None, category)
            )
        print("Book added successfully!")
    except sqlite3.IntegrityError:
        print("This ISBN already exists.")


def view_books():
    with sqlite3.connect(DB_NAME) as conn:
        books = conn.execute(
            "SELECT * FROM books ORDER BY title"
        ).fetchall()

    if not books:
        print("No books found.")
        return

    print("\nID | Title | Author | ISBN | Category | Status")
    for book in books:
        status = "Available" if book[5] else "Issued"
        print(
            f"{book[0]} | {book[1]} | {book[2]} | "
            f"{book[3] or '-'} | {book[4] or '-'} | {status}"
        )


def search_books():
    keyword = input("Enter title, author, ISBN, or category: ").strip()

    with sqlite3.connect(DB_NAME) as conn:
        books = conn.execute("""
            SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ?
               OR isbn LIKE ? OR category LIKE ?
        """, tuple([f"%{keyword}%"] * 4)).fetchall()

    if books:
        for book in books:
            status = "Available" if book[5] else "Issued"
            print(f"{book[0]} | {book[1]} | {book[2]} | {status}")
    else:
        print("No matching books found.")


def update_book():
    book_id = input("Enter book ID to update: ").strip()

    with sqlite3.connect(DB_NAME) as conn:
        book = conn.execute(
            "SELECT * FROM books WHERE id = ?", (book_id,)
        ).fetchone()

        if not book:
            print("Book not found.")
            return

        title = input(f"Title [{book[1]}]: ").strip() or book[1]
        author = input(f"Author [{book[2]}]: ").strip() or book[2]
        isbn = input(f"ISBN [{book[3] or '-'}]: ").strip() or book[3]
        category = input(
            f"Category [{book[4] or '-'}]: "
        ).strip() or book[4]

        try:
            conn.execute("""
                UPDATE books
                SET title = ?, author = ?, isbn = ?, category = ?
                WHERE id = ?
            """, (title, author, isbn, category, book_id))
            print("Book updated successfully!")
        except sqlite3.IntegrityError:
            print("That ISBN is already used by another book.")


def delete_book():
    book_id = input("Enter book ID to delete: ").strip()

    with sqlite3.connect(DB_NAME) as conn:
        book = conn.execute(
            "SELECT available FROM books WHERE id = ?", (book_id,)
        ).fetchone()

        if not book:
            print("Book not found.")
            return

        if not book[0]:
            print("Return the book before deleting it.")
            return

        conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        print("Book deleted successfully!")


def issue_book():
    book_id = input("Enter book ID to issue: ").strip()
    borrower = input("Enter borrower's name: ").strip()

    if not borrower:
        print("Borrower's name is required.")
        return

    with sqlite3.connect(DB_NAME) as conn:
        book = conn.execute(
            "SELECT available FROM books WHERE id = ?", (book_id,)
        ).fetchone()

        if not book:
            print("Book not found.")
        elif not book[0]:
            print("This book is already issued.")
        else:
            conn.execute(
                "UPDATE books SET available = 0 WHERE id = ?",
                (book_id,)
            )
            conn.execute(
                "INSERT INTO loans (book_id, borrower) VALUES (?, ?)",
                (book_id, borrower)
            )
            print("Book issued successfully!")


def return_book():
    book_id = input("Enter book ID to return: ").strip()

    with sqlite3.connect(DB_NAME) as conn:
        loan = conn.execute("""
            SELECT id FROM loans
            WHERE book_id = ? AND return_date IS NULL
            ORDER BY id DESC LIMIT 1
        """, (book_id,)).fetchone()

        if not loan:
            print("No active issue record found.")
            return

        conn.execute("""
            UPDATE loans
            SET return_date = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (loan[0],))
        conn.execute(
            "UPDATE books SET available = 1 WHERE id = ?",
            (book_id,)
        )
        print("Book returned successfully!")


def loan_history():
    with sqlite3.connect(DB_NAME) as conn:
        records = conn.execute("""
            SELECT loans.id, books.title, loans.borrower,
                   loans.issue_date, loans.return_date
            FROM loans
            JOIN books ON loans.book_id = books.id
            ORDER BY loans.id DESC
        """).fetchall()

    if not records:
        print("No loan history found.")
        return

    for record in records:
        status = record[4] or "Not returned"
        print(
            f"Loan {record[0]} | {record[1]} | "
            f"{record[2]} | Issued: {record[3]} | Returned: {status}"
        )


def reports():
    with sqlite3.connect(DB_NAME) as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM books"
        ).fetchone()[0]
        available = conn.execute(
            "SELECT COUNT(*) FROM books WHERE available = 1"
        ).fetchone()[0]
        issued = conn.execute(
            "SELECT COUNT(*) FROM books WHERE available = 0"
        ).fetchone()[0]

    print("\n--- Library Report ---")
    print("Total books:", total)
    print("Available books:", available)
    print("Issued books:", issued)


def main():
    setup_database()

    while True:
        print("\n===== LIBRARY MANAGEMENT SYSTEM =====")
        print("1. Add Book")
        print("2. View All Books")
        print("3. Search Books")
        print("4. Update Book")
        print("5. Delete Book")
        print("6. Issue Book")
        print("7. Return Book")
        print("8. Loan History")
        print("9. Reports")
        print("0. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            add_book()
        elif choice == "2":
            view_books()
        elif choice == "3":
            search_books()
        elif choice == "4":
            update_book()
        elif choice == "5":
            delete_book()
        elif choice == "6":
            issue_book()
        elif choice == "7":
            return_book()
        elif choice == "8":
            loan_history()
        elif choice == "9":
            reports()
        elif choice == "0":
            print("Thank you for using the Library Management System!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
