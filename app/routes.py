from flask import render_template, request, jsonify
from app import app
import requests
import json

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/user/<username>")
def api_user(username):
    r = requests.get(f"https://lichess.org/api/user/{username}")
    if r.status_code == 404:
        return {"error": "user_not_found"}, 404
    r.raise_for_status()
    return jsonify(r.json())

@app.route("/api/stats/<username>")
def api_stats(username):
    # Fetch games from 2025 (timestamp for Jan 1 2025)
    url = f"https://lichess.org/api/games/user/{username}"
    params = {
        "since": 1735689600000, 
        "pgnInJson": "true",
        "opening": "true",
        "max": 2000
    }
    headers = { "Accept": "application/x-ndjson" }
    
    try:
        r = requests.get(url, params=params, headers=headers)
        r.raise_for_status()
        
        text = r.text.strip()
        if not text:
            return {"error": "no_games_found"}, 404
            
        games = [json.loads(line) for line in text.split('\n')]
        
        # Sort games by date
        games.sort(key=lambda x: x.get('createdAt', 0))
        
        stats = calculate_stats(games, username.lower())
        return jsonify(stats)
    
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500

def calculate_stats(games, username):
    openings = {}
    opponents = {}
    time_controls = {}
    longest_game = {"moves": 0, "game_id": None}
    
    current_win_streak = 0
    current_lose_streak = 0
    max_win_streak = 0
    max_lose_streak = 0
    
    # Rating Journey Logic
    start_rating = None
    end_rating = None
    
    for game in games:
        # 1. Identify User Color
        white_user = game['players']['white'].get('user', {})
        black_user = game['players']['black'].get('user', {})
        is_white = white_user.get('id', '').lower() == username
        
        # 2. Get Rating (Start/End)
        user_rating = game['players']['white'].get('rating') if is_white else game['players']['black'].get('rating')
        if user_rating and isinstance(user_rating, int):
            if start_rating is None: start_rating = user_rating
            end_rating = user_rating

        # 3. Openings
        if game.get('opening'):
            opening_name = game['opening'].get('name', 'Unknown')
            # Simplify opening name (remove variation)
            simple_name = opening_name.split(':')[0].split(',')[0]
            openings[simple_name] = openings.get(simple_name, 0) + 1
        
        # 4. Opponents
        opponent_data = black_user if is_white else white_user
        opponent_name = opponent_data.get('name', 'Anonymous')
        if opponent_name != "Anonymous":
            opponents[opponent_name] = opponents.get(opponent_name, 0) + 1
        
        # 5. Time Control
        tc = game.get('speed', 'unknown')
        time_controls[tc] = time_controls.get(tc, 0) + 1
        
        # 6. Longest Game
        moves = len(game.get('moves', '').split())
        if moves > longest_game['moves']:
            longest_game = {'moves': moves, 'game_id': game.get('id')}
        
        # 7. Streaks
        winner = game.get('winner')
        user_won = (is_white and winner == 'white') or (not is_white and winner == 'black')
        user_lost = (is_white and winner == 'black') or (not is_white and winner == 'white')
        
        if user_won:
            current_win_streak += 1
            current_lose_streak = 0
            max_win_streak = max(max_win_streak, current_win_streak)
        elif user_lost:
            current_lose_streak += 1
            current_win_streak = 0
            max_lose_streak = max(max_lose_streak, current_lose_streak)
        else:
            current_win_streak = 0
            current_lose_streak = 0

    # Sort Aggregates
    top_openings = sorted(openings.items(), key=lambda x: x[1], reverse=True)[:5]
    top_opponents = sorted(opponents.items(), key=lambda x: x[1], reverse=True)[:5]
    favorite_tc = sorted(time_controls.items(), key=lambda x: x[1], reverse=True)[0] if time_controls else ('unknown', 0)
            
    return {
        'totalGames': len(games),
        'topOpenings': [{'name': name, 'count': count} for name, count in top_openings],
        'topOpponents': [{'name': name, 'count': count} for name, count in top_opponents],
        'maxWinStreak': max_win_streak,
        'maxLoseStreak': max_lose_streak,
        'favoriteTimeControl': {'name': favorite_tc[0], 'count': favorite_tc[1]},
        'longestGame': longest_game['moves'],
        'ratingJourney': {
            'start': start_rating or 0,
            'end': end_rating or 0,
            'diff': (end_rating or 0) - (start_rating or 0)
        },
    }