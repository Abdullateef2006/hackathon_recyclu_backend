# ♻️ Recyclable Project - Complete Documentation

A comprehensive recycling and sustainability platform that incentivizes eco-friendly behavior through coin rewards, AI-powered recycling detection, and company partnerships.

---

## 🌟 Core Features

### 🔐 User Management & Authentication
- User Registration & Login with JWT tokens  
- Referral System with bonus coins for inviting friends  
- User Profiles with personal details and banking information  
- PIN Security for coin withdrawals  
- Country-based User Organization  

### 💰 Coin Economy System
- Coin Earnings through recycling activities  
- Coin Validation by verified companies  
- Withdrawal System to convert coins to cash  
- Transaction History tracking all coin movements  
- Leaderboard showcasing top recyclers  

### 🤖 AI-Powered Recycling Detection
- Image Recognition using **Nyckel AI** to identify recyclable materials  
- Automatic Coin Rewards (**10 coins per recyclable item**)  
- Confidence Scoring with **80%+ threshold** for accuracy  
- **Cloudinary Integration** for image storage  

### 🏢 Company Management
- Company Registration with license verification  
- Admin Approval System for company verification  
- Coin Validation Services for users  
- User Management for company-attached accounts  

### 🔔 Real-time Notifications
- WebSocket Integration for live updates  
- Email Notifications for important events  
- Notification Center with read/unread status  
- Multiple Notification Types (validation, withdrawal, etc.)  

### 📊 Transaction & Analytics
- Complete Audit Trail for all coin transactions  
- Referral Bonuses tracking  
- Withdrawal Request System with email alerts  
- User Activity Monitoring  

---

## 🛠️ Technology Stack

**Backend Framework**  
- Django 4.2+ - Web framework  
- Django REST Framework - API development  
- Simple JWT - Token authentication  
- PostgreSQL/SQLite - Database  

**AI & File Management**  
- Nyckel AI - Image classification for recycling detection  
- Cloudinary - Image storage and CDN  
- Pillow - Image processing  

**Real-time Features**  
- Django Channels - WebSocket support  
- Redis - Channel layer for real-time communication  

**Email & Notifications**  
- Django Email Backend - SMTP email services  
- WebSocket - Real-time browser notifications  

**API Documentation**  
- DRF Spectacular - OpenAPI 3.0 documentation  
- Swagger UI - Interactive API documentation  

---

## 📋 Prerequisites
- Python 3.8+  
- Django 4.2+  
- Redis (for WebSocket functionality)  
- Cloudinary account (for image storage)  
- Nyckel account (for AI image classification)  
- SMTP email service (Gmail, SendGrid, etc.)  

---

## 🛣️ API Endpoints

### Authentication
- `POST /api/register/` - User registration with referral support  
- `POST /api/login/` - JWT token authentication  
- `POST /api/company/register/` - Company registration  
- `POST /api/company/login/` - Company authentication  

### User Management
- `GET /api/profile/` - Get user profile  
- `PUT /api/profile/` - Update user profile  
- `GET /api/countries/` - List available countries  

### Recycling System
- `POST /api/check-recyclable/` - Upload image for recycling detection  
- `GET /api/transaction-history/` - View coin transactions  
- `GET /api/leaderboard/` - Top recyclers leaderboard  

### Coin Management
- `POST /api/withdraw/` - Withdraw coins to bank account  
- `POST /api/validate-coins/{user_id}/` - Company validates user coins  
- `GET /api/unattached-users/` - List users without companies  

### Company Features
- `POST /api/company/register/` - Register new company  
- `GET /api/unattached-users/` - Browse potential customers  
- `POST /api/validate-coins/` - Validate user coins  

### Notifications
- `GET /api/notifications/` - User notifications  
- `POST /api/notifications/{id}/read/` - Mark as read  
- `GET /api/websocket-info/` - WebSocket connection details  

---

## ⚙️ Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/Abdullateef2006/hackathon_recyclu_backend
   cd recyclable-project

      ```bash
   Create a virtual environment

python -m venv env
source env/bin/activate  # on Windows use `env\Scripts\activate`
   ```bash
Install dependencies

pip install -r requirements.txt
   ```bash
python manage.py migrate

   ```bash
python manage.py createsuperuser

   ```bash
python manage.py runserver


