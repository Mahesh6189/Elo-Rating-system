from flask import Flask, render_template, request, redirect, url_for
import csv
import os

app = Flask(__name__)

# Constants for Elo calculation
K = 32

# Function to calculate Elo
def calculate_elo(player_rating, opponent_rating, result):
    expected_score = 1 / (1 + 10 ** ((opponent_rating - player_rating) / 400))
    new_rating = player_rating + K * (result - expected_score)
    return round(new_rating)

# Load players from CSV
def load_players(filename='players.csv'):
    players = {}
    if os.path.exists(filename):
        with open(filename, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                players[row['ID']] = {
                    'Name': row['Name'],
                    'Rating': int(row['Rating']),
                    'Matches Played': int(row['Matches Played']),
                    'Wins': int(row['Wins']),
                    'Losses': int(row['Losses']),
                    'Draws': int(row['Draws']),
                }
    return players

# Save players back to CSV
def save_players(players, filename='players.csv'):
    with open(filename, mode='w', newline='') as file:
        fieldnames = ['ID', 'Name', 'Rating', 'Matches Played', 'Wins', 'Losses', 'Draws']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for player_id, details in players.items():
            writer.writerow({
                'ID': player_id,
                'Name': details['Name'],
                'Rating': details['Rating'],
                'Matches Played': details['Matches Played'],
                'Wins': details['Wins'],
                'Losses': details['Losses'],
                'Draws': details['Draws'],
            })

# Function to calculate win rate percentage
def calculate_win_rate(wins, matches_played):
    return round((wins / matches_played) * 100) if matches_played > 0 else 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    players = load_players()
    if request.method == 'POST':
        player_id = request.form['player_id']
        name = request.form['name']

        if player_id in players:
            return render_template('add_player.html', error="Player ID already exists!")

        players[player_id] = {
            'Name': name,
            'Rating': 1200,
            'Matches Played': 0,
            'Wins': 0,
            'Losses': 0,
            'Draws': 0,
        }
        save_players(players)
        return redirect(url_for('index'))

    return render_template('add_player.html')

@app.route('/record_match', methods=['GET', 'POST'])
def record_match():
    players = load_players()
    if request.method == 'POST':
        player1_id = request.form['player1_id']
        player2_id = request.form['player2_id']
        result = float(request.form['result'])  # 1 for win, 0 for loss, 0.5 for draw

        if player1_id not in players or player2_id not in players:
            return render_template('record_match.html', error="One or both players not found!")

        if player1_id == player2_id:
            return render_template('record_match.html', error="Players cannot be the same!")

        # Update ratings
        new_rating1 = calculate_elo(players[player1_id]['Rating'], players[player2_id]['Rating'], result)
        new_rating2 = calculate_elo(players[player2_id]['Rating'], players[player1_id]['Rating'], 1 - result)
        players[player1_id]['Rating'] = new_rating1
        players[player2_id]['Rating'] = new_rating2

        # Update statistics
        players[player1_id]['Matches Played'] += 1
        players[player2_id]['Matches Played'] += 1

        if result == 1:
            players[player1_id]['Wins'] += 1
            players[player2_id]['Losses'] += 1
        elif result == 0:
            players[player1_id]['Losses'] += 1
            players[player2_id]['Wins'] += 1
        else:
            players[player1_id]['Draws'] += 1
            players[player2_id]['Draws'] += 1

        save_players(players)

        # Calculate win rate percentage
        win_rate_player1 = calculate_win_rate(players[player1_id]['Wins'], players[player1_id]['Matches Played'])
        win_rate_player2 = calculate_win_rate(players[player2_id]['Wins'], players[player2_id]['Matches Played'])

        return render_template('record_match.html', 
                               success=f"Updated Ratings: {player1_id}: {new_rating1}, {player2_id}: {new_rating2}, "
                                       f"{player1_id} Win Rate: {win_rate_player1}%, {player2_id} Win Rate: {win_rate_player2}%")

    return render_template('record_match.html')

@app.route('/view_ratings')
def view_ratings():
    players = load_players()
    return render_template('view_ratings.html', players=players)

@app.route('/delete_player', methods=['GET', 'POST'])
def delete_player():
    players = load_players()

    if request.method == 'POST':
        player_id = request.form['player_id']

        if player_id not in players:
            return render_template('delete_player.html', error="Player ID not found!")

        del players[player_id]
        save_players(players)

        return redirect(url_for('index'))

    return render_template('delete_player.html')

@app.route('/check_random', methods=['GET', 'POST'])
def check_random():
    if request.method == 'POST':
        player1_name = request.form['player1_name']
        player1_rating = int(request.form['player1_rating'])
        player2_name = request.form['player2_name']
        player2_rating = int(request.form['player2_rating'])
        status = request.form['status']

        result = 1 if status == "win" else 0 if status == "loss" else 0.5
        new_rating1 = calculate_elo(player1_rating, player2_rating, result)
        new_rating2 = calculate_elo(player2_rating, player1_rating, 1 - result)

        return render_template('check_random.html', 
                               new_rating1=new_rating1, new_rating2=new_rating2,
                               player1_name=player1_name, player2_name=player2_name)

    return render_template('check_random.html')


if __name__ == "__main__":
    app.run(debug=True)
