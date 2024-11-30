from flask import Flask, render_template, redirect, url_for, request, session, flash
from werkzeug.security import generate_password_hash
from pymongo import MongoClient
from bson import ObjectId
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Flask에서 flash 메시지를 사용하기 위해 secret_key 필요

# MongoDB 연결 설정
client = MongoClient('mongodb://localhost:3041/')
db = client['sports_game']  # 데이터베이스 이름 설정
users_collection = db['user']  # 유저 정보 저장하는 컬렉션
players_collection = db['player']  # 선수 정보 저장하는 컬렉션
match_summary_collection = db['match_summary']
marketplace_collection = db['marketplace']
match_lineup_collection = db['match_lineup']
# 로그인 페이지
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('menu'))
    return render_template('login.html')

# 회원가입 페이지
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get user input
        username = request.form['username']
        password = request.form['password']
        
        # Check if username already exists
        existing_user = users_collection.find_one({"username": username})
        if existing_user:
            flash('Username already exists, please choose a different one.', 'danger')
            return redirect(url_for('signup'))
        
        # Hash the password before storing it
        hashed_password = generate_password_hash(password)

        # Create new user document
        user = {
            "username": username,
            "password": hashed_password
        }
        
        # Insert the new user into the database
        users_collection.insert_one(user)
        
        flash('You have successfully registered! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

# 로그인 처리
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = users_collection.find_one({"username": username, "password": password})
    
    if user:
        session['user_id'] = str(user['_id'])  # 로그인한 유저의 ID를 session에 저장
        return redirect(url_for('menu'))
    else:
        return "Invalid username or password", 400

# 메뉴 페이지
@app.route('/menu')
def menu():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    return render_template('menu.html')

# 거래 페이지
@app.route('/trade')
def trade():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 장터에서 판매 중인 선수들 가져오기
    trade_items = marketplace_collection.find()  # marketplace 테이블에서 선수 정보 가져오기
    
    return render_template('trade.html', trade_items=trade_items)

# 선수 거래 처리
@app.route('/trade/<player_id>', methods=['POST'])
def buy_player(player_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    buyer_id = session['user_id']
    
    # 거래할 선수 정보 가져오기
    trade_item = marketplace_collection.find_one({"player_id": player_id})  # marketplace에서 해당 거래 아이템 가져오기
    buyer = users_collection.find_one({"_id": ObjectId(buyer_id)})  # 구매자 정보 가져오기

    if trade_item and buyer:
        price = trade_item['price']  # 선수의 가격
        seller_id = trade_item['listed_by']  # 판매자 ID
        seller = users_collection.find_one({"_id": ObjectId(seller_id)})  # 판매자 정보 가져오기

        # 구매자가 충분한 돈을 가지고 있는지 확인
        if buyer['money'] >= price:
            # 구매자 돈 차감 및 선수 추가
            users_collection.update_one(
                {"_id": ObjectId(buyer_id)},
                {"$inc": {"money": -price}, "$push": {"players": trade_item['player_id']}}
            )
            
            # 판매자에게 금액 추가
            if seller:  # 판매자가 유효한 경우
                users_collection.update_one(
                    {"_id": ObjectId(seller_id)},
                    {"$inc": {"money": price}}
                )
            
            # 선수의 소유자를 구매자로 변경
            players_collection.update_one(
                {"_id": ObjectId(trade_item['player_id'])},
                {"$set": {"owner_id": ObjectId(buyer_id)}}
            )

            # 장터에서 해당 거래 아이템 제거
            marketplace_collection.delete_one({"player_id": player_id})

            return redirect(url_for('menu'))
        else:
            return "Not enough money", 400
    else:
        return "Invalid player or user", 400

# 경기 페이지
@app.route('/match')
def match():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 랜덤으로 상대방 유저 선정
    opponents = users_collection.find({"_id": {"$ne": ObjectId(session['user_id'])}})  # 자신 제외
    opponent = random.choice(list(opponents))

    # 랜덤으로 승패 결정
    score_team_1 = random.randint(0, 5)
    score_team_2 = random.randint(0, 5)
    
    # 경기 기록 저장
    match_summary_collection.insert_one({
        "team_1": ObjectId(session['user_id']),
        "team_2": ObjectId(opponent['_id']),
        "score_team_1": score_team_1,
        "score_team_2": score_team_2,
        "match_date": datetime.now()
    })
    
    # 경기 결과를 화면에 출력
    return render_template('match_result.html', 
                           opponent=opponent, 
                           score_team_1=score_team_1, 
                           score_team_2=score_team_2)

# 경기 이력 페이지
@app.route('/match_history')
def match_history():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = ObjectId(session['user_id'])
    
    # 로그인한 유저가 참여한 경기들 가져오기
    match_history = list(match_summary_collection.find({
        "$or": [
            {"team_1": user_id},
            {"team_2": user_id}
        ]
    }))
    
    # 각 경기에 대해 결과 계산 추가
    for match in match_history:
        if match['team_1'] == user_id:
            match['result'] = (
                "Win" if match['score_team_1'] > match['score_team_2'] else 
                "Lose" if match['score_team_1'] < match['score_team_2'] else 
                "Draw"
            )
        elif match['team_2'] == user_id:
            match['result'] = (
                "Win" if match['score_team_2'] > match['score_team_1'] else 
                "Lose" if match['score_team_2'] < match['score_team_1'] else 
                "Draw"
            )
        else:
            match['result'] = "Unknown"
    
    return render_template('match_history.html', matches=match_history)

# 장터 등록 페이지
@app.route('/sell_player', methods=['GET', 'POST'])
def sell_player():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']

    # 유저의 owned_players 목록 가져오기
    user = users_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        return "User not found", 404
    
    # 소유한 선수들 가져오기
    owned_player_ids = user.get("owned_players", [])

    # 출전 중인 선수의 ID를 찾기
    user_lineup = match_lineup_collection.find_one({"player_id": user_id})
    lineup_player_ids = []
    if user_lineup:
        lineup_player_ids = [player['player_id'] for player in user_lineup['lineup']]

    # 유저가 소유한 선수 목록 가져오기 (출전 중인 선수는 제외)
    owned_players = list(players_collection.find(
        {"_id": {"$in": owned_player_ids}, "_id": {"$nin": lineup_player_ids}}
    ))

    if request.method == 'POST':
        player_id = request.form.get('player_id')
        price = int(request.form.get('price'))

        # 선수 존재 여부 확인
        player = players_collection.find_one({"_id": ObjectId(player_id), "owner_id": ObjectId(user_id)})

        if not player:
            return "Invalid player selected.", 400
        
        # 장터에 선수 등록
        marketplace_collection.insert_one({
            "player_id": player_id,
            "price": price,
            "listed_by": user_id,
            "listed_at": datetime.now()
        })
        
        return redirect(url_for('menu'))
    
    return render_template('sell_player.html', players=owned_players)

# 선수 출전 변경 페이지
@app.route('/change_lineup', methods=['GET', 'POST'])
def change_lineup():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']

    # 장터에 등록된 선수들의 ID를 가져옵니다 (해당 유저가 올린 선수만)
    marketplace_player_ids = [
        item['player_id'] for item in marketplace_collection.find({"listed_by": ObjectId(user_id)})
    ]
    
    # 사용자의 소유 선수 가져오기 (장터에 등록된 선수는 제외)
    owned_players = list(players_collection.find({
        "owner_id": ObjectId(user_id),
        "_id": {"$nin": marketplace_player_ids}  # 장터에 등록된 선수는 제외
    }))

    if request.method == 'POST':
        # 선택된 선수 가져오기
        selected_players = request.form.getlist('selected_players')
        
        if len(selected_players) != 3:
            return "You must select exactly 3 players for your lineup.", 400
        
        # 기존 라인업 삭제 후 새 라인업 저장
        match_lineup_collection.delete_one({"player_id": user_id})
        match_lineup_collection.insert_one({
            "match_id": f"M_{user_id}",
            "player_id": user_id,
            "lineup": [{"player_id": pid} for pid in selected_players]
        })
        
        return redirect(url_for('menu'))
    
    return render_template('change_lineup.html', players=owned_players)

# 로그아웃 처리
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # 로그아웃 시 세션 정보 삭제
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
