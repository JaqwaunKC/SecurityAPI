# train_model.py
import pandas as pd
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Enhanced dataset with extreme cases for high and low risk
data = {
    'is_tor_exit_node': [1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0,
                         1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1,
                         1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
    'request_frequency': [5, 150, 10, 10, 200, 30, 20, 5, 2, 300, 10, 220, 5, 300, 90, 500, 3, 600, 700, 5,
                          50, 600, 25, 300, 45, 3, 10, 500, 95, 1000, 2, 800, 15, 900, 1000, 5, 80, 5, 100, 30,
                          5, 500, 5, 600, 100, 1, 5, 5, 300, 5, 600, 1000, 15, 3, 5, 55, 110, 10, 45, 700],
    'country_risk_score': [5, 30, 5, 5, 25, 10, 40, 50, 5, 5, 50, 40, 5, 50, 5, 60, 5, 50, 60, 5,
                           25, 50, 10, 10, 40, 50, 5, 5, 10, 5, 60, 50, 10, 5, 10, 60, 5, 5, 60, 5,
                           5, 5, 5, 60, 5, 10, 10, 60, 10, 5, 60, 10, 10, 50, 5, 50, 10, 5, 10, 5],
    'risk_level': [1, 2, 0, 0, 2, 1, 1, 0, 1, 2, 0, 2, 1, 2, 1, 2, 0, 1, 2, 0,
                   1, 0, 1, 1, 1, 0, 2, 1, 2, 0, 1, 0, 2, 1, 2, 0, 0, 2, 1, 0,
                   2, 0, 1, 0, 2, 2, 0, 0, 1, 1, 2, 2, 1, 0, 2, 0, 1, 2, 0, 2]
}

# Ensure all lists have the same length
df = pd.DataFrame(data)

# Define features and target variable
X = df[['is_tor_exit_node', 'request_frequency', 'country_risk_score']]
y = df['risk_level']

# Scale numerical features
scaler = StandardScaler()
X[['request_frequency', 'country_risk_score']] = scaler.fit_transform(X[['request_frequency', 'country_risk_score']])

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

# Train a GradientBoostingClassifier
model = GradientBoostingClassifier(random_state=42)
model.fit(X_train, y_train)

# Test the model and display evaluation metrics
y_pred = model.predict(X_test)
print("Model Accuracy:", accuracy_score(y_test, y_pred))
print("Classification Report:\n", classification_report(y_test, y_pred))

# Save the trained model and scaler to files
joblib.dump(model, 'risk_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
print("Model saved as 'risk_model.pkl' and scaler saved as 'scaler.pkl'")
