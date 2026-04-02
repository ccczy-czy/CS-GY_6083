import os
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, abort

app: Flask = Flask(__name__)

DB_CONFIG: dict[str, str] = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5434"),
    "dbname": os.environ.get("DB_NAME", "flights_db"),
    "user": os.environ.get("DB_USER", "flights_user"),
    "password": os.environ.get("DB_PASSWORD", "flights_pass"),
}

def get_connection() -> psycopg2.extensions.connection:
    return psycopg2.connect(**DB_CONFIG)

@app.route("/", methods=["GET"])
def index() -> str:    
    airports: list[psycopg2.extras.RealDictRow] = []
    error: str | None = None

    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT airport_code, name, city, country
                    FROM Airport
                    ORDER BY airport_code
                    """
                )
                airports = cur.fetchall()
    except psycopg2.Error as exc:
        error = f"Database error: {exc}"

    return render_template("index.html", airports=airports, error=error)


@app.route("/flights", methods=["GET"])
def flights() -> str:    
    origin: str = request.args.get("origin", "").strip().upper()
    destination: str = request.args.get("destination", "").strip().upper()
    date_from: str = request.args.get("date_from", "").strip()
    date_to: str = request.args.get("date_to", "").strip()

    missing: list[str] = [
        name
        for name, val in [
            ("origin", origin),
            ("destination", destination),
            ("date_from", date_from),
            ("date_to", date_to),
        ]
        if not val
    ]
    if missing:
        return render_template(
            "results.html",
            flights=[],
            origin=origin,
            destination=destination,
            date_from=date_from,
            date_to=date_to,
            error=f"Missing required parameters: {', '.join(missing)}",
        )

    results: list[psycopg2.extras.RealDictRow] = []
    error: str | None = None

    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        f.flight_number,
                        f.departure_date,
                        fs.airline_name,
                        fs.origin_code,
                        fs.dest_code,
                        fs.departure_time,
                        fs.duration,
                        a.capacity,
                        COUNT(b.pid) AS booked_seats,
                        (a.capacity - COUNT(b.pid)) AS available_seats
                    FROM Flight f
                    JOIN FlightService fs
                        ON f.flight_number = fs.flight_number
                    JOIN Aircraft a
                        ON f.plane_type = a.plane_type
                    LEFT JOIN Booking b
                        ON f.flight_number = b.flight_number
                        AND f.departure_date = b.departure_date
                    WHERE fs.origin_code = %s
                      AND fs.dest_code   = %s
                      AND f.departure_date BETWEEN %s AND %s
                    GROUP BY
                        f.flight_number,
                        f.departure_date,
                        fs.airline_name,
                        fs.origin_code,
                        fs.dest_code,
                        fs.departure_time,
                        fs.duration,
                        a.capacity
                    ORDER BY f.departure_date, fs.departure_time
                    """,
                    (origin, destination, date_from, date_to),
                )
                results = cur.fetchall()
    except psycopg2.Error as exc:
        error = f"Database error: {exc}"

    return render_template(
        "results.html",
        flights=results,
        origin=origin,
        destination=destination,
        date_from=date_from,
        date_to=date_to,
        error=error,
    )

@app.route("/flights/<flight_number>/<departure_date>", methods=["GET"])
def flight_detail(flight_number: str, departure_date: str) -> str:    
    detail: psycopg2.extras.RealDictRow | None = None
    booked_seats: list[psycopg2.extras.RealDictRow] = []
    error: str | None = None

    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        f.flight_number,
                        f.departure_date,
                        f.plane_type,
                        fs.airline_name,
                        fs.origin_code,
                        fs.dest_code,
                        fs.departure_time,
                        fs.duration,
                        a.capacity,
                        COUNT(b.pid)            AS booked_seats,
                        (a.capacity - COUNT(b.pid)) AS available_seats
                    FROM Flight f
                    JOIN FlightService fs
                        ON f.flight_number = fs.flight_number
                    JOIN Aircraft a
                        ON f.plane_type = a.plane_type
                    LEFT JOIN Booking b
                        ON f.flight_number = b.flight_number
                        AND f.departure_date = b.departure_date
                    WHERE f.flight_number  = %s
                      AND f.departure_date = %s
                    GROUP BY
                        f.flight_number,
                        f.departure_date,
                        f.plane_type,
                        fs.airline_name,
                        fs.origin_code,
                        fs.dest_code,
                        fs.departure_time,
                        fs.duration,
                        a.capacity
                    """,
                    (flight_number, departure_date),
                )
                detail = cur.fetchone()

                if detail is None:
                    abort(404)

                cur.execute(
                    """
                    SELECT b.seat_number, p.passenger_name
                    FROM Booking b
                    JOIN Passenger p ON b.pid = p.pid
                    WHERE b.flight_number  = %s
                      AND b.departure_date = %s
                    ORDER BY b.seat_number
                    """,
                    (flight_number, departure_date),
                )
                booked_seats = cur.fetchall()

    except psycopg2.Error as exc:
        error = f"Database error: {exc}"

    return render_template(
        "flight_detail.html",
        detail=detail,
        booked_seats=booked_seats,
        error=error,
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
