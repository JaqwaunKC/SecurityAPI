import ipaddress
import logging
import os
import random
from datetime import datetime
import joblib
import pandas as pd
from flask import Flask, jsonify, request
from mysql.connector import pooling
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting for security
limiter = Limiter(get_remote_address, app=app, default_limits=["100 per hour", "20 per minute"])

# Database configuration using environment variables
db_config = {
    'user': os.getenv('DB_USER', 'flaskuser'),
    'password': os.getenv('DB_PASSWORD', 'yourpassword'),
    'host': os.getenv('DB_HOST', 'mysql' if os.getenv('DOCKER') else 'localhost'),
    'database': os.getenv('DB_NAME', 'tor_exit_nodes'),
    'pool_name': 'mypool',
    'pool_size': 5
}

# Load the ML model and scaler
model = joblib.load('risk_model.pkl')
scaler = joblib.load('scaler.pkl')

# Initialize a connection pool
connection_pool = pooling.MySQLConnectionPool(**db_config)

def get_db_connection():
    return connection_pool.get_connection()

def normalize_ip(ip):
    """Standardize IP format without compression for IPv6."""
    ip = ip.strip("[]")
    try:
        ip_obj = ipaddress.IPv4Address(ip)
        logger.info(f"Normalized IPv4 IP: {ip}")
        return str(ip_obj)
    except ipaddress.AddressValueError:
        pass

    try:
        ip_obj = ipaddress.IPv6Address(ip)
        ip = ip_obj.exploded  # Expand IPv6 to full notation
        logger.info(f"Normalized IPv6 IP: {ip}")
        return ip
    except ipaddress.AddressValueError:
        logger.warning(f"Invalid IP format provided: {ip}")
        return None

def is_valid_ip(ip):
    """Check if IP address is valid for both IPv4 and IPv6."""
    return normalize_ip(ip) is not None

def get_country_risk_score(country):
    high_risk_countries = ["CN", "RU", "IR", "KP"]
    return 30 if country in high_risk_countries else 5

def predict_risk_score(ip, is_tor_exit_node, request_frequency, country):
    """Calculate the risk score for an IP using the ML model."""
    try:
        logger.info(f"Values before prediction - is_tor_exit_node: {is_tor_exit_node}, request_frequency: {request_frequency}, country: {country}")

        if is_tor_exit_node is None or request_frequency is None or country is None:
            logger.error("Missing values for prediction inputs.")
            return 0, "Error", "Invalid data detected. Please review inputs."

        request_frequency = max(1, request_frequency + random.randint(-50, 100))
        country_risk_score = max(1, get_country_risk_score(country) + random.randint(-15, 15))

        input_data = pd.DataFrame({
            'is_tor_exit_node': [is_tor_exit_node],
            'request_frequency': [request_frequency],
            'country_risk_score': [country_risk_score]
        })

        if input_data.isnull().values.any():
            logger.error("Input data contains NaN values prior to scaling.")
            return 0, "Error", "Invalid data detected. Please review inputs."

        input_data[['request_frequency', 'country_risk_score']] = scaler.transform(
            input_data[['request_frequency', 'country_risk_score']]
        )

        risk_proba = model.predict_proba(input_data)[0][1]
        risk_score = int(risk_proba * 100)

        if risk_score < 25:
            risk_level = "Low"
            explanation = "Low risk based on low request frequency and country score."
        elif 25 <= risk_score < 65:
            risk_level = "Medium"
            explanation = "Medium risk due to moderate activity and/or country score."
        else:
            risk_level = "High"
            explanation = "High risk due to high activity and/or high-risk country."

        logger.info(f"Predicted probability: {risk_proba}, risk_score: {risk_score}, risk_level: {risk_level}")
        return risk_score, risk_level, explanation

    except ValueError as e:
        logger.error(f"Error in predict_risk_score: {e}")
        return 0, "Error", "Prediction error due to invalid input data."


@app.route('/')
def home():
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>Tor Exit Node Checker API</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; }
          h1 { color: #333; }
          .endpoint { margin-bottom: 20px; }
          input, button { padding: 8px; margin: 5px; }
          .results { margin-top: 20px; padding: 10px; background-color: #f4f4f4; border-radius: 4px; }
          .ip-columns { display: flex; gap: 20px; margin-top: 20px; }
          .column { flex: 1; }
          .column h3 { color: #333; }
          .column div { padding: 5px 0; }
        </style>
      </head>
      <body>
        <h1>Welcome to the Tor Exit Node Checker API</h1>
        <p>This API allows you to check if an IP address is a Tor exit node, view all Tor exit nodes, or delete specific IP addresses from the list.</p>

        <div class="endpoint">
          <h2>Available Endpoints:</h2>
          <div>
            <label for="checkIp">Check if IP is a Tor exit node:</label>
            <input type="text" id="checkIp" placeholder="Enter IP address">
            <button onclick="checkIp()">Check IP</button>
          </div>
          <div>
            <button onclick="listIps()">List All Tor Exit Nodes</button>
          </div>
          <div>
            <label for="deleteIp">Delete IP from the list:</label>
            <input type="text" id="deleteIp" placeholder="Enter IP address">
            <button onclick="deleteIp()">Delete IP</button>
          </div>
        </div>

        <div id="results" class="results"></div>

        <script>
          function displayResult(message) {
            document.getElementById("results").innerHTML = message;
          }

          function checkIp() {
            let ip = document.getElementById("checkIp").value.trim();
            if (!ip) return displayResult("Please enter an IP address to check.");
            if (ip.includes(":")) ip = `[${ip}]`;

            fetch(`/check_ip?ip=${encodeURIComponent(ip)}`)
              .then(response => response.json())
              .then(data => displayResult(data.message ? 
                `<strong>Result:</strong> ${data.message}` :
                `<strong>Result:</strong> The IP ${ip} is ${data.is_tor_exit_node ? '' : 'not'} a Tor exit node.<br>
                <strong>Risk Score:</strong> ${data.risk_score} (${data.risk_level})<br>
                <strong>Explanation:</strong> ${data.explanation}<br>
                <strong>Last Checked:</strong> ${data.last_checked}`
              ))
              .catch(() => displayResult("Error Checking IP"));
          }

          function listIps() {
            fetch(`/list_ips`)
              .then(response => response.json())
              .then(data => {
                const ipv4List = data.tor_exit_nodes.filter(ip => ip.indexOf(':') === -1).map(ip => `<div>${ip}</div>`).join("");
                const ipv6List = data.tor_exit_nodes.filter(ip => ip.indexOf(':') !== -1).map(ip => `<div>${ip}</div>`).join("");

                displayResult(`
                  <div class="ip-columns">
                    <div class="column"><h3>IPv4 Tor Exit Nodes</h3>${ipv4List || "<div>No IPv4 addresses found.</div>"}</div>
                    <div class="column"><h3>IPv6 Tor Exit Nodes</h3>${ipv6List || "<div>No IPv6 addresses found.</div>"}</div>
                  </div>
                `);
              })
              .catch(() => displayResult("Error listing IPs."));
          }

          function deleteIp() {
            const ip = document.getElementById("deleteIp").value.trim();
            if (!ip) return displayResult("Please enter an IP address to delete.");
            fetch(`/delete_ip?ip=${encodeURIComponent(ip)}`, { method: 'DELETE' })
              .then(response => response.json())
              .then(data => displayResult(data.status === 'deleted' ?
                `<strong>Status:</strong> The IP ${ip} has been deleted from the database.` :
                `<strong>Status:</strong> The IP ${ip} was <em>not</em> found in the database.`
              ))
              .catch(() => displayResult("Error deleting IP."));
          }
        </script>
      </body>
    </html>
    """

@app.route('/check_ip', methods=['GET'])
@limiter.limit("5 per minute")
def check_ip():
    ip = request.args.get('ip')
    if not ip:
        return jsonify({'error': 'IP address is required'}), 400

    normalized_ip = normalize_ip(ip)
    if normalized_ip is None:
        return jsonify({'error': 'A valid IP address is required'}), 400

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT is_tor_exit_node, request_frequency, country FROM ip_risk_scores WHERE ip = %s", (normalized_ip,))
            result = cursor.fetchone()
            if result:
                is_tor_exit_node, request_frequency, country = result
                if any(val is None for val in result):
                    logger.error(f"Retrieved data contains None values for IP {normalized_ip}")
                    return jsonify({'error': 'Incomplete data for IP'}), 400
                risk_score, risk_level, explanation = predict_risk_score(normalized_ip, is_tor_exit_node, request_frequency, country)
                return jsonify({
                    'is_tor_exit_node': bool(is_tor_exit_node),
                    'risk_score': risk_score,
                    'risk_level': risk_level,
                    'explanation': explanation,
                    'last_checked': timestamp
                })
            return jsonify({'message': f"The IP {normalized_ip} is not found in the database.", 'is_tor_exit_node': False, 'risk_score': 0, 'last_checked': timestamp})

