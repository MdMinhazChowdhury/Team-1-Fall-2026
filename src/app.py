
from flask import Flask, render_template, request, redirect, url_for

from src.person_b.auth_service import AuthService
from src.person_b.deck_service import DeckService
from src.person_c1.card_service import CardService

# Initialize authentication service
auth_service = AuthService()

# Initialize deck service
deck_service = DeckService(auth_service)

# Initialize flashcard service
card_service = CardService(deck_service)

# Initialize the Flask application.
# Our templates and static folders are located
# one level above this file.
app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static",
    static_url_path="/static"
)


# Homepage route
@app.route("/")
def home():
    return render_template("index.html")

# Login page
@app.route("/login", methods=["GET", "POST"])
def login():

    # Display the login page
    if request.method == "GET":
        return render_template("login.html")

    # Collect submitted login information
    username = request.form.get("username")
    password = request.form.get("password")

    # Authenticate using Person B's service
    user = auth_service.login(username, password)

    if user is not None:
        return redirect(url_for("dashboard"))

    # Login failed
    return render_template(
        "login.html",
        error="Invalid username or password."
    )

# Deck dashboard
@app.route("/dashboard")
def dashboard():

    try:
        # Retrieve decks belonging to the logged-in user
        decks = deck_service.list_decks()

        return render_template(
            "dashboard.html",
            decks=decks
        )

    except PermissionError:
        # Redirect users who are not logged in
        return redirect(url_for("login"))

# Create a new deck
@app.route("/create-deck", methods=["POST"])
def create_deck():

    title = request.form.get("title")
    description = request.form.get("description")

    try:
        deck_service.create_deck(title, description)
        return redirect(url_for("dashboard"))

    except PermissionError:
        return redirect(url_for("login"))

    except ValueError as error:
        decks = deck_service.list_decks()

        return render_template(
            "dashboard.html",
            decks=decks,
            error=str(error)
        )

# View a deck and its flashcards
@app.route("/deck/<deck_id>")
def view_deck(deck_id):

    try:
        deck = deck_service.get_deck(deck_id)
        cards = card_service.get_cards(deck_id)

        return render_template(
            "deck.html",
            deck=deck,
            cards=cards
        )

    except PermissionError:
        return redirect(url_for("login"))

# Create a new flashcard
@app.route("/deck/<deck_id>/add-card", methods=["POST"])
def add_card(deck_id):

    question = request.form.get("question")
    answer = request.form.get("answer")

    try:
        card_service.add_card(deck_id, question, answer)

        return redirect(
            url_for("view_deck", deck_id=deck_id)
        )

    except PermissionError:
        return redirect(url_for("login"))

    except ValueError as error:
        deck = deck_service.get_deck(deck_id)
        cards = card_service.get_cards(deck_id)

        return render_template(
            "deck.html",
            deck=deck,
            cards=cards,
            error=str(error)
        )

# Delete a flashcard
@app.route("/deck/<deck_id>/delete-card/<card_id>", methods=["POST"])
def delete_card(deck_id, card_id):

    try:
        card_service.delete_card(card_id)

        return redirect(
            url_for("view_deck", deck_id=deck_id)
        )

    except PermissionError:
        return redirect(url_for("login"))

# Edit an existing flashcard
@app.route("/deck/<deck_id>/edit-card/<card_id>", methods=["POST"])
def edit_card(deck_id, card_id):

    question = request.form.get("question")
    answer = request.form.get("answer")

    try:
        card_service.edit_card(card_id, question, answer)

        return redirect(
            url_for("view_deck", deck_id=deck_id)
        )

    except PermissionError:
        return redirect(url_for("login"))

    except ValueError as error:
        deck = deck_service.get_deck(deck_id)
        cards = card_service.get_cards(deck_id)

        return render_template(
            "deck.html",
            deck=deck,
            cards=cards,
            error=str(error)
        )

# Mark a flashcard as difficult
@app.route("/deck/<deck_id>/mark-difficult/<card_id>", methods=["POST"])
def mark_difficult(deck_id, card_id):

    try:
        card_service.mark_difficult(card_id)

        return redirect(
            url_for("view_deck", deck_id=deck_id)
        )

    except PermissionError:
        return redirect(url_for("login"))



# Registration page
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    try:
        auth_service.register(username, email, password)

        return redirect(url_for("login"))

    except ValueError as error:
        return render_template(
            "register.html",
            error=str(error)
        )

# Start the development server
if __name__ == "__main__":
    app.run(debug=True)
