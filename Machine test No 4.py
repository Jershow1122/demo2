import mysql.connector
from datetime import datetime, timedelta


class Database:
    def __init__(self, host='localhost', user='root', password='jershow', database='hotelsystem'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self.cursor = None

    def connect(self):
        if self.conn is not None:
            return
        self.conn = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )
        self.cursor = self.conn.cursor()

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def execute_query(self, query, params=()):
        self.connect()
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def execute_command(self, command, params=()):
        self.connect()
        self.cursor.execute(command, params)
        self.conn.commit()


def create_tables(db):
    db.execute_command('''
        CREATE TABLE IF NOT EXISTS Rooms (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category VARCHAR(50) NOT NULL,
            room_no VARCHAR(50) NOT NULL,
            rate_per_day DECIMAL(10, 2) NOT NULL,
            hourly_rate DECIMAL(10, 2)
        )
    ''')

    db.execute_command('''
        CREATE TABLE IF NOT EXISTS Customers (
            customer_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            contact VARCHAR(50) NOT NULL
        )
    ''')

    db.execute_command('''
        CREATE TABLE IF NOT EXISTS Bookings (
            booking_id VARCHAR(10) PRIMARY KEY,
            customer_id INT NOT NULL,
            room_id INT NOT NULL,
            date_of_booking DATE NOT NULL,
            date_of_occupancy DATE NOT NULL,
            no_of_days INT,
            no_of_hours INT,
            advance_received DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES Customers(customer_id),
            FOREIGN KEY(room_id) REFERENCES Rooms(id)
        )
    ''')

    db.execute_command('''
        CREATE TABLE IF NOT EXISTS Admin (
            username VARCHAR(50) PRIMARY KEY,
            password VARCHAR(50) NOT NULL
        )
    ''')

    # Insert default admin credentials
    db.execute_command('INSERT IGNORE INTO Admin (username, password) VALUES (%s, %s)', ('admin', 'admin123'))


def check_admin_credentials(db, username, password):
    result = db.execute_query('SELECT * FROM Admin WHERE username = %s AND password = %s', (username, password))
    return len(result) > 0


def generate_booking_id(db):
    # Generate a booking ID with a prefix and a 3-digit number
    prefix = 'BK'
    last_id = db.execute_query('SELECT booking_id FROM Bookings ORDER BY booking_id DESC LIMIT 1')
    if last_id:
        last_number = int(last_id[0][0][2:])
        new_number = last_number + 1
    else:
        new_number = 1
    return f"{prefix}{new_number:03}"


def main_menu(db):
    while True:
        print("\nAdmin Menu")
        print("1. Category wise list of rooms and their Rate per day")
        print("2. List of all rooms which are occupied for next two days")
        print("3. List of all rooms in increasing order of rate per day")
        print("4. Search Rooms now and display customer details")
        print("5. Update room when the customer leaves to Unoccupied")
        print("6. Rooms which are not booked")
        print("7. Store all records in file and display from file")
        print("8. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            display_rooms_by_category(db)
        elif choice == '2':
            list_occupied_rooms_for_next_two_days(db)
        elif choice == '3':
            display_rooms_sorted_by_rate(db)
        elif choice == '4':
            booking_id = input("Enter Booking ID: ")
            search_room_by_booking_id(db, booking_id)
        elif choice == '5':
            booking_id = input("Enter Booking ID to mark room as unoccupied: ")
            update_room_availability(db, booking_id)
        elif choice == '6':
            display_unoccupied_rooms(db)
        elif choice == '7':
            store_records_to_file(db)
            display_records_from_file()
        elif choice == '8':
            print("Exiting...")
            db.disconnect()
            break
        else:
            print("Invalid choice. Please try again.")


def display_rooms_by_category(db):
    # Fetch all rooms with their details
    rows = db.execute_query('SELECT id, category, room_no, rate_per_day, hourly_rate FROM Rooms ORDER BY category, room_no')

    for row in rows:
        room_id = row[0]
        category = row[1]
        room_no = row[2]
        rate_per_day = row[3]
        hourly_rate = row[4]

        # Determine the display values based on the category
        if category in ['convention_halls', 'ball_rooms']:
            # For convention halls and ballrooms, display hourly_rate and N/A for rate_per_day
            rate_per_day_display = "N/A"
            hourly_rate_display = hourly_rate if hourly_rate is not None else "N/A"
        else:
            # For other categories, display rate_per_day and N/A for hourly_rate
            rate_per_day_display = rate_per_day if rate_per_day is not None else "N/A"
            hourly_rate_display = hourly_rate if hourly_rate is not None else "N/A"

        print(f"Category: {category}, Room No: {room_no}, Rate per Day: {rate_per_day_display}, Hourly Rate: {hourly_rate_display}")

def list_occupied_rooms_for_next_two_days(db):
    today = datetime.now().strftime('%Y-%m-%d')
    two_days_later = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')

    rows = db.execute_query('''
        SELECT Rooms.room_no, Bookings.date_of_occupancy, Bookings.no_of_days
        FROM Rooms
        JOIN Bookings ON Rooms.id = Bookings.room_id
        WHERE (Bookings.date_of_occupancy <= %s AND
               DATE_ADD(Bookings.date_of_occupancy, INTERVAL Bookings.no_of_days DAY) >= %s)
    ''', (two_days_later, today))

    # Check if rows are empty and handle the case
    if rows:
        for row in rows:
            print(f"Room No: {row[0]}, Occupancy Start: {row[1]}, No. of Days: {row[2]}")
    else:
        print("No rooms are occupied for the next two days.")


def display_rooms_sorted_by_rate(db):
    rows = db.execute_query('SELECT category, room_no, rate_per_day FROM Rooms ORDER BY rate_per_day')

    for row in rows:
        category = row[0]
        room_no = row[1]
        rate_per_day = row[2]

        # Handle None values for rate_per_day
        if rate_per_day is None:
            rate_per_day_display = "N/A"
        else:
            rate_per_day_display = f"${rate_per_day:.2f}"

        print(f"Category: {category}, Room No: {room_no}, Rate per Day: {rate_per_day_display}")


def search_room_by_booking_id(db, booking_id):
    rows = db.execute_query('''
        SELECT Bookings.booking_id, Customers.name, Customers.contact, Rooms.room_no,
               Bookings.date_of_booking, Bookings.date_of_occupancy, Bookings.no_of_days, 
               Bookings.advance_received
        FROM Bookings
        JOIN Customers ON Bookings.customer_id = Customers.customer_id
        JOIN Rooms ON Bookings.room_id = Rooms.id
        WHERE Bookings.booking_id = %s
    ''', (booking_id,))

    if rows:
        row = rows[0]
        print(f"Booking ID: {row[0]}\nCustomer: {row[1]}\nContact: {row[2]}\nRoom No: {row[3]}")
        print(
            f"Date of Booking: {row[4]}\nDate of Occupancy: {row[5]}\nNo. of Days: {row[6]}\nAdvance Received: ${row[7]:.2f}")
    else:
        print("Booking ID not found.")


def display_unoccupied_rooms(db):
    # Fetch rooms that are not listed in the Bookings table
    rows = db.execute_query('''
        SELECT Rooms.id, Rooms.category, Rooms.room_no, Rooms.rate_per_day, Rooms.hourly_rate
        FROM Rooms
        LEFT JOIN Bookings ON Rooms.id = Bookings.room_id
        WHERE Bookings.room_id IS NULL
    ''')

    # Check if any rows are returned
    if rows:
        for row in rows:
            room_id = row[0]
            category = row[1]
            room_no = row[2]
            rate_per_day = row[3]
            hourly_rate = row[4]

            # Handle None values for rates
            rate_per_day_display = rate_per_day if rate_per_day is not None else "N/A"
            hourly_rate_display = hourly_rate if hourly_rate is not None else "N/A"

            print(f"Room ID: {room_id}, Category: {category}, Room No: {room_no}, Rate per Day: {rate_per_day_display}, Hourly Rate: {hourly_rate_display}")
    else:
        print("All rooms are currently booked.")


def update_room_availability(db, booking_id):
    db.execute_command('DELETE FROM Bookings WHERE booking_id = %s', (booking_id,))
    print(f"Booking ID {booking_id} has been removed successfully.")
    print("The List of occupied rooms list will be also updated")


def store_records_to_file(db):
    try:
        with open('rooms.txt', 'w') as f:
            rows = db.execute_query('SELECT * FROM Rooms')
            for row in rows:
                f.write(f"{row}\n")

        with open('customers.txt', 'w') as f:
            rows = db.execute_query('SELECT * FROM Customers')
            for row in rows:
                f.write(f"{row}\n")

        with open('bookings.txt', 'w') as f:
            rows = db.execute_query('SELECT * FROM Bookings')
            for row in rows:
                f.write(f"{row}\n")

    except Exception as e:
        print(f"Error writing to file: {e}")


def display_records_from_file():
    try:
        with open('rooms.txt', 'r') as f:
            print("Rooms:")
            print(f.read())

        with open('customers.txt', 'r') as f:
            print("Customers:")
            print(f.read())

        with open('bookings.txt', 'r') as f:
            print("Bookings:")
            print(f.read())

    except FileNotFoundError:
        print("One or more files not found.")
    except Exception as e:
        print(f"Error reading from file: {e}")


def login():
    db = Database()
    db.connect()
    username = input("Enter Username: ")
    password = input("Enter Password: ")

    if check_admin_credentials(db, username, password):
        print("Login successful!")
        main_menu(db)
    else:
        print("Invalid credentials. Please try again.")

    db.disconnect()


if __name__ == "__main__":
    db = Database(
        host='localhost',
        user='root',
        password='jershow',
        database='hotelsystem'
    )
    create_tables(db)
    login()
