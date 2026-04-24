from flask import Blueprint, jsonify, request
from .services import get_message, get_all_messages, add_message

main = Blueprint('main', __name__)

@main.route("/")
def home():
    return jsonify({"message": get_message()})

@main.route("/messages")
def messages():
    return jsonify({"messages": get_all_messages()})

@main.route("/messages", methods=["POST"])
def create_message():
    data = request.json
    text = data.get("text", "default message")
    add_message(text)
    return jsonify({"status": "ok", "text": text})