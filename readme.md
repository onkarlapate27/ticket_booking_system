# Railway Ticket Reservation System

A fully functional Railway Ticket Reservation API built using Django. This system handles ticket booking, berth assignment, cancellation, and automatic upgrades from RAC and Waitlist, ensuring constraints are maintained.

---

## Features

- Ticket Booking with berth preferences and prioritization.
- RAC and Waitlist handling with defined limits.
- Auto-upgrade mechanism on ticket cancellation.
- Child (under 5) passenger handling (no berth assignment).
- Rate limiting to prevent abuse (5 requests/min per user).

---

## System Constraints

| Category       | Limit |
|----------------|-------|
| Confirmed      | 63    |
| RAC (Side Lower)| 18   |
| Waitlist       | 10    |

---

## Berth Prioritization Logic

- **Senior Citizens (Age > 60)** and **Females with children < 5 years** are prioritized for **LOWER** berths.
- **General passengers** are assigned berths based on availability (LOWER → MIDDLE → UPPER → SIDE_LOWER → SIDE_UPPER).
- **RAC Passengers** always receive **SIDE_LOWER** berth.
- **Children under 5 years**: No berth assigned, but ticket is confirmed.

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/onkarlapate27/ticket_booking_system.git
cd ticket_booking
```

### 2. Create Virtual Environment & Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Apply Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Run the Development Server

```bash
python manage.py runserver
```

## Testing

```bash
python manage.py test
```

## Docker Setup

### Prerequisites

- Docker installed and running on your machine.

---

### Build Docker Image

Make sure you're in the project root directory where the `Dockerfile` is located.

```bash
# Build the Docker image
docker build -t railway-reservation .
```

## Build and run using Docker Compose
docker-compose up --build

## Stop containers
docker-compose down