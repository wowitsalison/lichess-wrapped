from flask import render_template, request, jsonify
from app import app
import requests
import json

# Home page
@app.route("/")
def index():
    return render_template("index.html")

# Get user profile by username
@app.route("/api/user/<username>")
def api_user(username):
    r = requests.get(f"https://lichess.org/api/user/{username}")
    
    if r.status_code == 404:
        return {"error": "user_not_found"}, 404
    
    r.raise_for_status()
    return jsonify(r.json())

# Get user game statistics
@app.route("/api/stats/<username>")
def api_stats(username):
    url = f"https://lichess.org/api/games/user/{username}"
    params = {
        "since": 1735689600000,
        "pgnInJson": "true",
        "opening": "true"
    }
    headers = {
        "Accept": "application/x-ndjson"
    }
    
    try:
        r = requests.get(url, params=params, headers=headers)
        r.raise_for_status()
        
        text = r.text.strip()
        if not text:
            return {"error": "no_games_found"}, 404
            
        games = [json.loads(line) for line in text.split('\n')]
        
        stats = calculate_stats(games, username.lower())
        return jsonify(stats)
    
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500

# Game statistics helper
def calculate_stats(games, username):
    openings = {}
    opponents = {}
    time_controls = {}
    longest_game = {"moves": 0, "game_id": None}
    current_win_streak = 0
    current_lose_streak = 0
    max_win_streak = 0
    max_lose_streak = 0
    
    for game in games:
        # Opening
        if game.get('opening'):
            opening_name = game['opening'].get('name', 'Unknown')
            openings[opening_name] = openings.get(opening_name, 0) + 1
        
        # Opponent
        white_user = game['players']['white'].get('user', {})
        black_user = game['players']['black'].get('user', {})
        is_white = white_user.get('id', '').lower() == username
        
        opponent = black_user.get('name', 'Anonymous') if is_white else white_user.get('name', 'Anonymous')
        if opponent != "Anonymous":
            opponents[opponent] = opponents.get(opponent, 0) + 1
        
        # Time control
        tc = game.get('speed', 'unknown')
        time_controls[tc] = time_controls.get(tc, 0) + 1
        
        # Longest game
        moves = len(game.get('moves', '').split())
        if moves > longest_game['moves']:
            longest_game = {'moves': moves, 'game_id': game.get('id')}
        
        # Win/lose streaks
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
    
    top_openings = sorted(openings.items(), key=lambda x: x[1], reverse=True)[:5]
    top_opponents = sorted(opponents.items(), key=lambda x: x[1], reverse=True)[:5]
    favorite_time_control = sorted(time_controls.items(), key=lambda x: x[1], reverse=True)[0] if time_controls else ('unknown', 0)
    
    return {
        'totalGames': len(games),
        'topOpenings': [{'name': name, 'count': count} for name, count in top_openings],
        'topOpponents': [{'name': name, 'count': count} for name, count in top_opponents],
        'maxWinStreak': max_win_streak,
        'maxLoseStreak': max_lose_streak,
        'favoriteTimeControl': {'name': favorite_time_control[0], 'count': favorite_time_control[1]},
        'longestGame': longest_game['moves']
    }