# Tor Exit Node Checker API

This project is a Flask-based API that allows users to check if an IP address is a Tor exit node, view all Tor exit nodes, or delete specific IP addresses from the list. It uses a machine learning model to predict the risk associated with an IP address based on specific features.

## Project Overview

This project accomplishes the following:
- **Checks IPs against a list of Tor exit nodes:** Updates the list of Tor nodes daily from a trusted source.
- **Predicts Risk Scores:** Based on a machine learning model that assigns risk levels to IP addresses based on activity.
- **Supports IPv4 and IPv6:** Recognizes and normalizes both IP versions.
- **Ensures Security:** Implements rate limiting and other best practices for API security.

## Key Features

1. **Check if IP is a Tor Exit Node**
2. **Risk Score Prediction using Machine Learning**
3. **Scheduled Refresh of Tor Exit Nodes**
4. **Supports both IPv4 and IPv6**
5. **Rate Limiting** to prevent abuse

## Future Improvements
Future improvements could include:
- **JWT Authentication** for secure user access.
- **Advanced CORS Policies** for domain-based access control.
- **Improved Rate Limiting** based on user roles.
  
These enhancements would add scalability and flexibility to the API, especially for production environments.

## Prerequisites

- **Docker** (for containerization)
- **Python 3.8+**
- **MySQL** (or MySQL Workbench)
- **Flask** and **APScheduler** (installed via pip)
- **Postman** (for testing the API)

## Installation

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd <repository-directory>
Step 2: Set Up Environment Variables
Create a .env file in the root directory to store sensitive information like database credentials. The environment variables should include:

makefile
Copy code
DB_USER=flaskuser
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_NAME=tor_exit_nodes
Step 3: Build Docker Container (Optional)
To run the app in Docker:

bash
Copy code
docker build -t tor_exit_checker .
docker run -p 8889:8889 --env-file .env tor_exit_checker
Step 4: Install Required Python Libraries
bash
Copy code
pip install -r requirements.txt
Step 5: Set Up MySQL Database
Create a MySQL database and a table with the necessary structure:

sql
Copy code
CREATE DATABASE tor_exit_nodes;
USE tor_exit_nodes;

CREATE TABLE IF NOT EXISTS tor_ips (
    ip VARCHAR(45) PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS ip_risk_scores (
    ip VARCHAR(45) PRIMARY KEY,
    is_tor_exit_node BOOLEAN,
    request_frequency INT DEFAULT 1,
    country VARCHAR(50),
    risk_score INT DEFAULT 0
);
How It Works
1. Scheduled Refresh of Tor Exit Nodes
The app fetches the latest list of Tor exit nodes daily at 6 PM and updates the MySQL database. The list is retrieved from Checkpoint’s IP list and contains both IPv4 and IPv6 addresses.

2. IP Normalization and Validation
The normalize_ip function ensures IP addresses conform to a standardized format. Both IPv4 and IPv6 addresses are supported, and the app validates each IP format.

3. Machine Learning Risk Prediction
Using a pre-trained machine learning model, the app assigns a risk score to each IP based on:

Whether it's a Tor exit node
Request frequency
Country risk score
4. Rate Limiting
The app implements rate limiting to protect the API against abuse:

10 requests per minute for /check_ip
5 requests per minute for /list_ips and /delete_ip
API Endpoints
GET /check_ip
Checks if a given IP address is a Tor exit node and provides its risk score.

Parameters: ip (query parameter)
Example Request: http://127.0.0.1:8889/check_ip?ip=[2001:0470:0001:0908:0000:0000:0000:9001]
Response:
json
Copy code
{
  "is_tor_exit_node": true,
  "risk_score": 45,
  "risk_level": "Medium",
  "explanation": "Medium risk due to moderate activity",
  "last_checked": "2024-10-31 18:00:00"
}
GET /list_ips
Retrieves all stored Tor exit nodes in the database, split between IPv4 and IPv6.

Example Request: http://127.0.0.1:8889/list_ips
Response:
json
Copy code
{
  "tor_exit_nodes": {
    "ipv4": ["192.0.2.1", "198.51.100.1"],
    "ipv6": ["2001:db8::1", "2001:db8::2"]
  }
}
DELETE /delete_ip
Deletes a specified IP from the list of Tor exit nodes.

Parameters: ip (query parameter)
Example Request: http://127.0.0.1:8889/delete_ip?ip=192.0.2.1
Response:
json
Copy code
{
  "status": "deleted"
}
Testing the API
Use Postman or curl to send requests to each endpoint:

bash
Copy code
curl -X GET "http://127.0.0.1:8889/check_ip?ip=[2001:0470:0001:0908:0000:0000:0000:9001]"
curl -X GET "http://127.0.0.1:8889/list_ips"
curl -X DELETE "http://127.0.0.1:8889/delete_ip?ip=192.0.2.1"