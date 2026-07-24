# GOHAR TRADERS – Inventory & Sales Management System

A complete, production-ready Inventory, Sales, Expense, Udhar (Credit), and Reporting system built specifically for small and medium trading businesses.

---

# 🚀 Tech Stack

| Layer | Technology |
|---------|------------|
| Frontend | HTML, CSS (Tailwind), JavaScript, Axios |
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL (Supabase) |
| Authentication | JWT (Access + Refresh Tokens) |
| ORM | SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Password Hashing | Argon2 |
| Containerization | Docker |
| Web Server | Nginx |

---

# 📦 Features

## Authentication

- User Signup
- User Login
- Forgot Password
- JWT Authentication
- Auto Token Refresh
- Maximum 5 User Accounts
- First Registered User becomes Owner

---

## Inventory Management

### Fixed Categories

- Cold Drinks
- Juices
- Eggs

### Product Management

- Dynamic Product Creation
- Brand Management
- Container Type Management
- Size Management
- Soft Delete Support

### Batch Management

- Auto Generated Batch Numbers
- Purchase Price Tracking
- Selling Price Tracking
- Remaining Stock Tracking
- Batch Completion Detection

---

## FIFO Sales Engine

- Automatic FIFO Stock Consumption
- Multi-Batch Sale Handling
- Accurate Cost of Goods Sold (COGS)
- Real-Time Stock Updates
- Inventory Locking During Sales

---

## Expense Management

- Shop Expenses
- Home Expenses
- Date Filtering
- Expense Deletion
- Expense Analytics

---

## Udhar (Credit) Management

### Receivable Entries

- Customer Credit
- Partial Payments
- Settlement Tracking

### Payable Entries

- Supplier Payments
- Outstanding Balances
- Payment History

---

## Reports

- Sales Reports
- Profit & Loss Reports
- Expense Reports
- Category Reports
- Brand Reports
- Batch Reports
- Inventory Valuation Reports
- Remaining Stock Reports

---

## Dashboard

Real-Time Dashboard Metrics:

- Today's Revenue
- Today's Profit
- Total Inventory Value
- Low Stock Alerts
- Active Udhar Records
- Pending Payments
- Recent Sales
- Completed Batch Notifications

---

## Security Features

- Argon2 Password Hashing
- JWT Authentication
- Role-Based Access Control
- Input Validation
- Protected API Endpoints
- Audit Logging
- Soft Deletes

---

## User Roles

### Owner

Full Access:

- Manage Users
- Manage Inventory
- Manage Sales
- Manage Expenses
- Manage Udhar
- Access Reports
- Delete Records

### Staff

Limited Access:

- Create Sales
- Add Inventory
- Add Expenses
- Add Udhar Entries

Restricted From:

- Deleting Critical Records
- System Administration

---

# 📁 Project Structure

```text
shop-management/
│
├── backend/
│   ├── routers/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── security.py
│   ├── dependencies.py
│   ├── config.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
│
├── frontend/
│   ├── js/
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   ├── inventory.html
│   ├── sales.html
│   ├── expenses.html
│   ├── reports.html
│   ├── udhar.html
│   ├── forgot-password.html
│   └── Dockerfile
│
├── .gitignore
└── README.md
```

---

# ⚙️ Environment Variables

Create a `.env` file inside the backend folder.

```env
SUPABASE_DB_URL=YOUR_SUPABASE_POOLER_CONNECTION_STRING
SECRET_KEY=YOUR_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256
```

Example:

```env
SUPABASE_DB_URL=postgresql://postgres.PROJECT_REF:PASSWORD@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
SECRET_KEY=your-long-random-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256
```

⚠️ Never upload your `.env` file to GitHub.

---

# 🏃 Running Application (Docker)

## Build Backend

```bash
docker build -t gohar-backend ./backend
```

## Build Frontend

```bash
docker build -t gohar-frontend ./frontend
```

---

## Start Backend Container

```bash
docker run -d --name gohar-backend-container -p 8000:8000 gohar-backend
```

---

## Start Frontend Container

```bash
docker run -d --name gohar-frontend-container -p 3000:80 gohar-frontend
```

---

## Stop Backend

```bash
docker stop gohar-backend-container
```

---

## Stop Frontend

```bash
docker stop gohar-frontend-container
```

---

## Start Existing Containers Again

```bash
docker start gohar-backend-container
docker start gohar-frontend-container
```

---

## Remove Containers

```bash
docker rm gohar-backend-container
docker rm gohar-frontend-container
```

---

# 🌐 Service URLs

## Frontend

```text
http://localhost:3000/login.html
```

---

## Backend API

```text
http://localhost:8000
```

---

## Swagger API Documentation

```text
http://localhost:8000/docs
```

---

## Health Check

```text
http://localhost:8000/health
```

Expected Response:

```json
{
  "status": "ok",
  "database": "connected"
}
```

---

# 🧪 Application Workflow

1. User Login
2. Dashboard Loads
3. Inventory Creation
4. Batch Addition
5. Product Sales
6. FIFO Consumption
7. Expense Tracking
8. Udhar Tracking
9. Reports Generation
10. Profit/Loss Analysis

---

# 🗄 Database

Database Provider:

```text
Supabase PostgreSQL
```

Connection Method:

```text
Supabase Pooler (IPv4 Compatible)
```

Benefits:

- Stable Docker Connectivity
- Connection Pooling
- Better Scalability
- Production Ready

---

# 📄 API Modules

## Auth

- Signup
- Login
- Refresh Token
- Forgot Password
- Reset Password

## Inventory

- Categories
- Products
- Batches

## Sales

- Create Sale
- View Sales

## Expenses

- Add Expense
- View Expenses
- Delete Expense

## Udhar

- Create Udhar
- Payments
- Settlements

## Reports

- Revenue Reports
- Profit Reports
- Inventory Reports

## Dashboard

- Real-Time Analytics

---

# 🐛 Troubleshooting

## Database Connection Error

If you see:

```text
Network is unreachable
```

Use:

```text
Supabase Pooler Connection String
```

instead of:

```text
db.project.supabase.co
```

---

## Login Issues

Verify:

- Backend Container Running
- Frontend Container Running
- Database Connected
- JWT Token Generated

---

## Docker Container Not Running

Check:

```bash
docker ps
```

View Logs:

```bash
docker logs gohar-backend-container
docker logs gohar-frontend-container
```

---

# 🚀 Production Deployment

Current Setup:

```text
Frontend Container
        ↓
FastAPI Backend Container
        ↓
Supabase PostgreSQL
```

Suitable For:

- Retail Shops
- Grocery Stores
- Beverage Distributors
- Small Trading Businesses

---

# 👨‍💻 Developed By

Awais Ismail

Powered by Zenvora AI

---

# 📃 License

All Rights Reserved.

This software is proprietary and may not be redistributed without permission.